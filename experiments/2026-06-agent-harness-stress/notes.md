# 2026-06-agent-harness-stress

Second attempt to find the regime where the structured harness from
[Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
actually *helps*. v1 (`../2026-06-agent-harness`) was a ceiling null — Sonnet one-shot a
10-feature toy, so the long-horizon failure mode never engaged. Here I changed the two levers
most likely to engage it, within the same <$10 budget:

1. **Weaker model under test:** `claude-haiku-4-5-20251001` (scaffolding tends to help weaker
   models more).
2. **Longer horizon + tighter budget:** 20 features (2× v1) and an 80k-token per-run cap
   (v1 was 120k), so a bloated transcript can exhaust the budget before finishing.

Single variable unchanged: `harness.strategy` ∈ {naive, structured}. Same model, tools,
task, budget for both arms.

## Results (2026-06-15, 3 seeds each)

| Metric | Baseline (naive) | Intervention (structured) | Delta | Distributions |
| --- | --- | --- | --- | --- |
| features_passed | 20.0 ± 0.0 | **7.67 ± 0.47** | **−12.3** | non-overlapping (20 vs ~8) |
| pass_rate | 1.00 | 0.38 | −0.62 | non-overlapping |
| total_tokens | 12,165 ± 125 | 83,343 ± 1,530 | +5.9× | non-overlapping |
| est_cost_usd | $0.022 | $0.120 | +5.3× | non-overlapping |
| budget_hit | False (0/3) | **True (3/3)** | — | — |

Stress-round spend: ≈ $0.55. Cumulative across v1 + stress: ≈ $1.7.

### Verdict: the intervention is STRICTLY DOMINATED here — fewer features *and* higher cost.
The result flipped relative to the article's claim. Haiku, like Sonnet, **one-shots all 20
independent functions** in a single ~12k-token session (20/20, every seed). The structured
harness instead pays per-feature overhead — each session re-injects the growing `solution.py`
and re-runs all 20 checks — so it **burned the entire 80k-token budget after only ~8
features** (budget_hit on every seed). Same budget, ~5.9× the tokens, less than half the task.

### Why this still isn't a refutation of the article
The decisive fact is that the task remained **one-shot-able even for Haiku**. The article's
mechanism only pays off when the task **cannot** be done in one pass — when the horizon is
long enough that a monolithic context degrades (context rot, regressions, window overflow).
Twenty independent utility functions never reach that regime; they just expose the harness's
fixed overhead, which a tight budget then turns into a hard penalty.

So across two honest attempts (v1 easy/ceiling, v2 harder/tighter/weaker-model), the
structured harness was **equal-or-worse**, because neither task could escape the one-shot
regime. Demonstrating the *positive* claim requires a genuinely non-one-shot task — large,
interacting, regression-prone features that force many sessions of real incremental work —
which costs well beyond this budget.

### What would actually engage the failure mode (next step, not run)
- Features that **interact / can regress** (later edits break earlier ones), so the monolithic
  agent loses coherence as context grows and the structured arm's per-session re-verification
  earns its keep.
- A horizon large enough that the naive transcript exceeds the context window.
- Both push cost past $10; flagged, not run.
