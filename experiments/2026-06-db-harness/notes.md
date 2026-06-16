# 2026-06-db-harness

Third and most serious attempt to test the
[long-running-agent harness](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
claim — this time on a task that is genuinely **non-one-shot and interacting**: build a
~500-line mini in-memory SQL engine, 30 features (SELECT/WHERE/JOIN/GROUP BY/aggregates/...),
where a shared parser+evaluator means a bug in one path can break many features.

## Design
- **Single variable:** `harness.strategy` ∈ {naive (one session), structured (one feature per
  session, context reset to a compact documented state)}. Same tools, task, and per-run token
  budget for both arms.
- **Second axis:** model — Haiku 4.5 (4 seeds, primary) and Sonnet 4.6 (2 seeds, sanity).
- **Grading:** each feature's SQL battery is run against the agent's engine and a reference
  engine (`shared/_db_reference.py`); pass iff results match. Grader validated: correct→30/30,
  empty→0/30, single injected bug caught, order/type tolerant.
- **Metrics:** features passed, **regressions** (peak − final), tokens, cost. 3 seeds+ each.
- **Hard $24 USD kill-switch** (file ledger) spanning the whole sweep.

## Results (2026-06-15/16)

| Model | Arm | features passed (mean ± std) | regressions | tokens (mean) | hit token cap? | $/run |
| --- | --- | --- | --- | --- | --- | --- |
| Haiku 4.5 | naive | **19.2 ± 11.5**  (28, 21, 28, **0**) | 0 | 527k | 4/4 | $0.73 |
| Haiku 4.5 | structured | **12.2 ± 1.1**  (12, 11, 12, 14) | 0 | 507k | 4/4 | $0.67 |
| Sonnet 4.6 | naive | **30.0 ± 0.0**  (30, 30) | 0 | 260k | 0/2 | $1.00 |
| Sonnet 4.6 | structured | **29.5 ± 0.5**  (30, 29) | 0 | 503k | 2/2 | $1.71 |

Total sweep spend: **$11.46** (of $24 cap). All 12 runs completed.

## Verdict: the structured harness did NOT improve outcomes at any scale tested.

**On the capable model (Sonnet):** both arms essentially solve the task (30 vs 29.5), but
structured costs **1.7×** the tokens and was very slightly worse — it hit the token cap near
the end (one feature short on a seed). Pure overhead. Same shape as the v1/v2 toy results.

**On the weak model (Haiku):** the two arms differ, but **not in structured's favor on the
mean**:
- naive has the higher ceiling — 3 of 4 runs hit 21–28/30 — but is **unreliable**: one run
  catastrophically scored **0/30** (it built a 503-line engine with a broken `SELECT` path and
  never recovered in a single session). Genuine failure, not a harness artifact (verified).
- structured is **consistent but token-starved**: it hit the 500k cap after only ~12 of 30
  feature-sessions, because re-injecting the growing engine + contract each session is ~2×
  less token-efficient. Its low score is a budget artifact, not a capability plateau.

**The headline mechanism never fired.** The article's core promise is that clean state per
session prevents the regressions/context-rot that sink long naive runs. We observed **zero
regressions in all 12 runs** (peak == final everywhere). The one catastrophic naive failure
was a core-path bug it couldn't debug in one session — not gradual regression — and structured
"avoided" catastrophe partly by never attempting past feature ~12.

So: no reproduction of the claimed benefit. Structured is strictly more expensive per feature;
on a capable model that buys nothing, and on a weak model it buys consistency only by doing
less. The regression-prevention effect the harness is built around produced no measurable
signal here.

## Honest caveats / what would change this
- **Equal-budget control throttled structured.** It hit the 500k cap in all 6 runs and never
  finished. A fairer test of "can structured *complete* the task" needs a much larger token
  budget — but that abandons the equal-budget control and costs more. Open question:
  token-starved vs genuinely incapable.
- **n is small** (Haiku 4, Sonnet 2). The most interesting number — naive's catastrophic
  failure rate — rests on a single 0/30. It could be ~10% or ~40%; can't tell at n=4. More
  Haiku naive seeds would resolve it cheaply (~$0.7 each) and is the highest-value follow-up.
- **Still far from the article's regime** (Opus 4.5, 200+ features, hours). 30 features is a
  miniature; the long-horizon context-rot that motivates the harness may only bite well beyond
  this scale.
