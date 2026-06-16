# 2026-06-agent-harness

Testing the central pattern of Anthropic's
[Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents).

## What the article actually claims
It makes **no quantitative claim** — no benchmark, no success rate, no %. It argues
*qualitatively* that a structured harness (initializer + **one-feature-per-session** coding
agent that leaves **clean, documented state**: a feature list, a progress log, commits,
verification each session) lets agents build large apps over long horizons, where a naive
high-level prompt fails. Model used in the article: Opus 4.5; task: a 200+-feature web app.

## Operationalized, testable claim (mine, not theirs)
> Holding model, tools, task, and total token budget fixed, a **structured** harness
> (one feature per session, context reset to a compact documented state) completes **more**
> objectively-graded features than a **naive** harness (all features in one session, whose
> transcript grows every turn).

Mechanism under test: clean state per session → smaller per-turn context → more useful
work per token, within a fixed budget.

## Setup
- **Model under test:** `claude-sonnet-4-6`, temperature 1.0.
- **Task:** build `solution.py`, a pure-Python utility lib with 10 independent features
  (`task/features.yaml`), each graded by a deterministic check in `shared/agent_eval.py`.
- **Single variable:** `harness.strategy` ∈ {`naive`, `structured`}. Configs are identical
  otherwise (`config.yaml` vs `config.intervention.yaml`).
- **Controls:** same model, tools (`write_file/read_file/list_files/run_tests`), same hard
  per-run token cap (`budget.max_total_tokens`, equal for both arms — this neutralizes the
  "structured just gets more compute" confound).
- **Seeds:** [0,1,2] — each an independent stochastic agent run. **Note:** LLM agent runs
  are *not* bit-reproducible; a "seed" indexes an independent sample, not a deterministic
  replay. The manifest still pins config + git commit + env + pip freeze.
- **Metric:** features passing (mean ± std). Secondary: tokens spent, sessions, turns.

## Reusable vs experiment-local
- Reusable (in `shared/`): `agent.py` (agent loop, tools, budget, the two strategies),
  `agent_eval.py` (grader), `runner.py` (seeds/manifest/results). Imported, not copied.
- Experiment-local: `config*.yaml`, `task/features.yaml`, `intervention.py` (entrypoint),
  `results/`.

## Cost control (budget ceiling: under $10)
- Hard per-run token cap (default 120k). Worst case 3 seeds × 2 arms × 120k = 720k tokens
  ≈ $2–5 on Sonnet. A 1-seed/3-feature `config.smoke.yaml` measures real cost first.
- Runs bill the Anthropic API directly (needs `ANTHROPIC_API_KEY`). No GPU / Modal involved.

## Offline verification done (no spend)
- Imports clean; 10 features load; empty workspace grades **0/10**; a correct reference
  solution grades **12/12** → grader is sound and not trivially passable.

## Risks / what would change the conclusion
- **Ceiling effect:** Sonnet may pass 10/10 in both arms on this easy task → null. (Mitigate
  by tightening the token cap and/or raising `n_features` so the naive transcript bloat
  bites.)
- **External validity:** 10 pure-Python functions ≠ a 200-feature web app with browser
  verification. A clean win here says little about that scale, and vice-versa. Stated plainly
  in any writeup.
- **Grader design** is mine; both arms graded identically, but the task choice itself is a
  lever.

## Results (2026-06-15, claude-sonnet-4-6, 3 seeds each)

| Metric | Baseline (naive) | Intervention (structured) | Delta | Distributions |
| --- | --- | --- | --- | --- |
| features_passed | 10.0 ± 0.0 | 10.0 ± 0.0 | 0 | identical (both point masses at 10/10) |
| pass_rate | 1.00 | 1.00 | 0 | identical |
| total_tokens | 8,095 ± 294 | 74,907 ± 1,373 | **+8.3×** | far apart, non-overlapping |
| est_cost_usd | $0.042 ± 0.002 | $0.335 ± 0.007 | **+8.0×** | far apart, non-overlapping |
| sessions / turns | 1 / 3 | 10 / 30 | — | by construction |

Total experiment spend (incl. smoke): ≈ **$1.15**. No run hit its token cap.

### Verdict: NULL on quality; structured is pure overhead at this scale.
Both harnesses solved the task perfectly (10/10, zero variance), so there is **no quality
signal** to compare — the distributions are identical. The only measurable difference is
cost: the structured harness spent **~8× more tokens and 10× more turns to reach the same
outcome**.

This is **not** a refutation of the article. Its claim lives in a regime — 200+ features
over hours — where the monolithic transcript grows long enough to degrade the model
(context rot, regressions, window pressure). The smoke test confirmed empirically that
Sonnet **one-shots** 10 tiny functions in a single turn, so that long-horizon failure mode
**never engages here**. Below the horizon where context bloat bites, the structured harness's
clean-state-per-session machinery is cost with no payoff.

The honest, postable finding: **at a scale a <$10 budget can reach, the harness's benefit is
not reproducible — and its overhead is real.** Confirming the *positive* claim would require a
genuinely long-horizon task (large N, interacting/regression-prone features) that costs far
more than this budget. That was the Phase-1 risk; the data bore it out.

### What would change this conclusion
- A task large enough that the naive transcript exceeds the window / induces regressions.
- A weaker model that fails the monolithic approach but is rescued by incremental sessions.
- Measuring *quality degradation over horizon*, not pass/fail on independent toy features.
