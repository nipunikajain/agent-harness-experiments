# TokenPilot: Cache-Efficient Context Management for LLM Agents — replication notes

**Paper:** [arXiv:2606.17016](https://arxiv.org/abs/2606.17016) · **Date run:** 2026-07-08 ·
**Model:** claude-haiku-4-5-20251001 · **Backend:** local (API-bound, no GPU)

## The claim
TokenPilot is an inference-time context-management framework for long-horizon LLM agents. Three
mechanisms: (1) **Prefix Stabilization** — replace volatile runtime markers with static
placeholders so the prompt prefix is byte-identical and stays cache-resident; (2) **Observation
Reduction** — deterministic rules strip HTML / truncate / dedupe tool outputs before ingestion;
(3) **Lifecycle-Aware Eviction** — purge completed context segments in batches so the prefix isn't
mutated mid-stream. Paper's headline: **cost ↓ 56–87%** vs a "Vanilla" (no-management) agent while
**task accuracy stays competitive**, cost measured in billed dollars decomposed into cache-hit /
cache-miss / output tokens.

Provenance check (done 2026-07-08): the paper is credible. It is from Ningyu Zhang's group at
Zhejiang University and builds on their prior, verifiable LightMem paper ([arXiv:2510.18866](https://arxiv.org/abs/2510.18866),
overlapping authors). It is a legitimate preprint, safe to cite. However, I did not have access to
their exact models or private benchmarks (PinchBench, Claw-Eval) to reproduce their numbers
directly. So this is **not** a re-run of their setup. It is a **directional test of the mechanism**
on a real cache-aware API (Claude Haiku 4.5), which returns the exact `cache_read_input_tokens` /
`cache_creation_input_tokens` fields TokenPilot reads.

## What I built
- **Task (fixed, shared by all three arms; `tasks.py`):** a long-horizon *referral-chain* task. Each
  question is a chain of 4 registry-record documents; the start id is given, each record's main
  content points to the next record's id, and the final record names a destination city (the exact
  answer). Solving = open 4 docs in pointer order + submit. Each doc is ~3 KB of noisy HTML (nav,
  cookie banner, scripts, footer) with the routing line in a `<main>` region. 5 questions/seed.
- **Single variable:** `tokenpilot.enabled` (baseline `false` → intervention `true`). Identical
  model, tasks, tools, seeds, and prompt-caching setup otherwise.
- **Both main arms (baseline and TokenPilot) use standard Anthropic prompt caching** (cache breakpoint
  on the static system+tools prefix + a rolling breakpoint on the growing conversation). The baseline
  is a *competent cache-using agent*, **not** a no-cache strawman. On top of it, TokenPilot adds all
  three mechanisms. This makes the controlled baseline-vs-TokenPilot gap a **conservative** read of the
  paper's claim. (The third arm, Vanilla, deliberately disables caching — see Results.)
- **Cost** = real Haiku 4.5 billing computed from the API's own usage metadata:
  input $1.00/M, cache-write $1.25/M, cache-read $0.10/M, output $5.00/M.
- Reuses the shared runner (`shared/runner.py` — logs resolved config, seeds, git commit, env,
  pip-freeze; 3 seeds; raw per-seed JSON) and the file-backed USD kill-switch (`shared/agent.py`).

## Result (3 seeds each, THREE arms)

Two arms form the controlled one-variable comparison (`config.yaml` vs `config.intervention.yaml`,
differing only in `tokenpilot.enabled`). A third **reference** arm (`config.vanilla_nocache.yaml`)
disables prompt caching entirely — this is the no-management "Vanilla" agent the paper compares to.

| arm | cost / 5-task run (USD) | accuracy | cache hit-rate | cost range |
| --- | --- | --- | --- | --- |
| **Vanilla** (no caching, raw obs) — *paper's reference* | 0.15286 ± 8e-5 | 1.00 | 0.00 | [0.15278, 0.15297] |
| **Baseline** (competent, cache-using, raw obs) | 0.06505 ± 3e-5 | 1.00 | 0.75 | [0.06501, 0.06508] |
| **TokenPilot** (cache + reduction + eviction) | 0.04676 ± 4.2e-3 | 1.00 | 0.81 | [0.04162, 0.05181] |

All arms: accuracy **1.00 on every seed**, 5 turns/task. Every pairwise cost distribution is disjoint.

### The number depends entirely on which baseline you pick
- **Vanilla → TokenPilot: −69.4%.** This is the paper-comparable comparison, and it lands **inside
  the paper's claimed 56–87% band.** Directional claim replicates.
- **…but 57.4 of those points are just turning on prompt caching** (Vanilla → Baseline = −57.4%),
  which any competent engineer already does and which is not TokenPilot's contribution.
- **Baseline → TokenPilot: −28.1%.** This is TokenPilot's *actual* incremental value — its
  observation-reduction + prefix-stabilization + eviction, measured over an agent that already
  caches. It comes from ~37% fewer cache-write tokens (reduced observations; stable prefix written
  once vs. re-written per task) and ~12% fewer cache-read tokens (smaller accumulated context).

**Verdict: replicates against the paper's own baseline (−69%, in-band), but ~⅘ of the headline is
prompt caching, not context management. TokenPilot's net contribution over a cache-using agent is
~28%, with zero accuracy loss at this scale.**

## Honest caveats / where a choice changes the conclusion
1. **Baseline strength drives the magnitude — now measured, not asserted.** Against no-cache Vanilla
   the reduction is −69% (in the paper's band); against a cache-using baseline it is −28%. The 41-point
   difference is prompt caching, which any competent agent already has. Reporting only the −69% would
   credit TokenPilot for caching it didn't invent; reporting only the −28% would undersell it vs. the
   paper's stated baseline. Both are in the notes on purpose.
2. **The mechanism can REVERSE below the provider's cache threshold.** Haiku 4.5 only caches prefixes
   above ~4.1k tokens. In an earlier run with a ~3.4k-token system prompt, observation reduction kept
   TokenPilot's prompt *under* the threshold so it never cached, while the baseline's larger raw
   transcripts *crossed* it and did cache — making TokenPilot **more expensive** ($0.0207 vs
   $0.0146/task). I sized the (genuine, ~4.3k-token) system prompt above the threshold so caching is
   active for both, which is the fair comparison — but the reversal is real and setup-dependent.
3. **The headline % is a function of setup, not a constant.** It scales with cacheable-prefix size,
   observation size/noisiness, and chain length. My noisy docs and 4-hop chains are favorable to
   reduction; less noisy tools or shorter horizons shrink the gap. The paper's % is equally
   setup-dependent.
4. **Two levers are bundled, not separated.** `tokenpilot.enabled` toggles prefix-stabilization +
   observation-reduction + eviction together (matching "framework vs Vanilla"). Eviction barely fires
   at 4-hop chains. I did not run a per-lever ablation.
5. **Accuracy under harsher reduction — now tested (stress sweep, `results/stress_reduction.json`).**
   I swept the reducer's truncation budget from safe to brutal, cutting *below* the answer line
   (which sits at ~char 142), 3 seeds each:

   | reducer cutoff | accuracy | cost / run | avg turns | recover() calls / run |
   | --- | --- | --- | --- | --- |
   | 600 chars (default, keeps answer) | 1.00 | $0.022* | 5.0 | 0 |
   | 130 chars (cuts answer line) | 1.00 | $0.064* | 9.0 | 20 |
   | 70 chars | 1.00 | $0.067* | 9.0 | 20 |
   | 35 chars (destroys content) | 1.00 | $0.066* | 9.0 | 20 |

   **Accuracy never broke — it stayed 1.00 even when reduction destroyed the answer line.** Why: the
   agent sees the "…[truncated; use recover()]" marker and calls `recover()` to pull the full
   document. TokenPilot's recovery tool is a real safety net that protects correctness. **But the
   cost win evaporates and reverses:** past the sweet spot the agent re-fetches every document (20
   recover calls = all 4 docs × 5 tasks), turns nearly double (5→9), and cost triples. Over-reducing
   is self-defeating — you pay more than if you hadn't reduced at all. So the real lesson isn't
   "reduction risks accuracy" (the safety net covers that); it's "**there's a sweet spot, and past it
   reduction costs you money, not answers.**"
   *Absolute costs in this sweep are lower than the main table (warm prompt cache carried over between
   back-to-back runs); the trend across cutoffs is the robust part, not the absolute dollars.*
6. **Provider-side caching is nondeterministic** (5-min TTL, load-dependent), which is why TokenPilot's
   cost std (4.2e-3) is ~100× the baseline's — its cross-task cache reuse sometimes doesn't land.

## Reproduce
```bash
cd ml-experiments
python -m shared.runner --experiment experiments/2026-07-tokenpilot --config config.yaml               # baseline (cache)
python -m shared.runner --experiment experiments/2026-07-tokenpilot --config config.intervention.yaml   # TokenPilot
python -m shared.runner --experiment experiments/2026-07-tokenpilot --config config.vanilla_nocache.yaml # Vanilla (no cache)
```
Total API spend for the whole investigation (all smoke/threshold probes + the 3 arms + the stress
sweep): **$1.64**.
Raw per-seed results + manifests (git commit, seeds, env, pip-freeze) in `results/`.
