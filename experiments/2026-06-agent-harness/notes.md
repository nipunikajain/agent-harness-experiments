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

## Results
_(filled in after Phase 3 run)_
