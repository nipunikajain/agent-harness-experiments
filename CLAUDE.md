# CLAUDE.md

This repo tests whether AI/LLM research claims actually hold, with enough rigor to publish.
Reusable harness in `shared/`, one folder per experiment under `experiments/`, results tracked
in the README scoreboard. `/test-paper` triages a paper or technique and runs it through the
shared harness.

## Discovery → test → scoreboard pipeline

A human-gated pipeline. Agents discover and propose; the human decides everything else. There
is deliberately **no central orchestrator or manager agent — the glue is the human**.

1. **Scout proposes.** `/scout-research` (the `research-scout` subagent) scans configured
   sources, dedupes against the scoreboard and `queue.md`, and appends candidates to `queue.md`
   as `proposed — awaiting review`. `/scout-skills` (the `skill-scout` subagent) proposes
   skills the agents could use. Scouts run nothing and install nothing.
2. **I pick.** I read `queue.md` and choose an entry.
3. **/test-paper triages and STOPS.** I run `/test-paper <link>` myself. It does Phase-1
   triage (claim, minimal reproduction, cost, honest risk) and waits. No code, no spend yet.
4. **I approve.** Only then does it build the harness and run the experiment.
5. **It runs; I write the verdict.**
6. **Scoreboard updates.** A one-row summary lands in the `README.md` table.

## The gate (non-negotiable)

**Agents discover and propose. The human decides anything that costs money, adds executable
capability, or goes public.** Concretely, agents never: install a skill or package, run
`/test-paper`, start an experiment, spend on compute, or push/publish. Those are the human's
calls. The scouts are tool-restricted (no shell) to enforce this structurally, not just by
instruction.

## Where things live

- Proposals queue: `queue.md`
- Scout sources (editable): `.claude/scout/sources.yaml`
- Subagents: `.claude/agents/research-scout.md`, `.claude/agents/skill-scout.md`
- Invoke the scouts: `/scout-research`, `/scout-skills`
- Experiment command: `/test-paper`  ·  Scoreboard: the table in `README.md`

## Scheduled runs: queue.md commits auto-merge

A scheduled routine runs `/scout-research`, commits the `queue.md` additions to a `claude/`
branch, opens a PR, and **merges it immediately** — no human look before it lands in `master`.
This is a deliberate, narrow exception to the no-push/publish gate above, scoped to exactly
one case: a PR whose only change is an append to `queue.md` from a scout run. It does not
extend to any other PR (experiment code, harness changes, scoreboard edits) — those stay
human-gated as usual.

Rationale: merging doesn't skip the actual review step — the human still reads `queue.md` and
picks an entry at step 2 of the pipeline, regardless of whether the file lives in `master` or
an open PR. Since the repo has no CI gating merges, and GitHub's native auto-merge requires a
repo setting ("Allow auto-merge") that isn't enabled, the merge is done directly
(`merge_pull_request`) rather than via GitHub's auto-merge feature.

To avoid conflicts (rather than resolving them after the fact): before pushing, rebase the
`claude/` branch onto the latest `master`. Since `queue.md` is append-only, this should make
conflicts structurally rare-to-impossible. If a real conflict still occurs, do not
auto-resolve it — stop and leave the PR open for human review instead of guessing.
