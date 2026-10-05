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
   as `proposed — awaiting review`, opened as a PR. `/scout-skills` (the `skill-scout`
   subagent) proposes skills the agents could use. Scouts run nothing and install nothing.
   Scout PRs auto-merge once the `validate-scout-pr` CI check passes (see below) — that check
   only lets the diff through if it's a pure addition to `queue.md` and touches no other file,
   so auto-merge never lands anything beyond a proposal. Review still happens; it just happens
   at step 2, on the merged file, instead of gating the merge itself.
2. **I pick.** I read `queue.md` and choose an entry.
3. **/test-paper triages and STOPS.** I run `/test-paper <link>` myself. It does Phase-1
   triage (claim, minimal reproduction, cost, honest risk) and waits. No code, no spend yet.
4. **I approve.** Only then does it build the harness and run the experiment.
5. **It runs; I write the verdict.**
6. **Scoreboard updates.** A one-row summary lands in the `README.md` table.

## The gate (non-negotiable)

**Agents discover and propose. The human decides anything that costs money, adds executable
capability, or goes public.** Concretely, agents never: install a skill or package, run
`/test-paper`, start an experiment, spend on compute, or publish results. Those are the
human's calls. The scouts are tool-restricted (no shell) to enforce this structurally, not
just by instruction.

The one narrow exception is landing a scout's own proposal-only PR (see step 1) — CI-gated to
a pure `queue.md` addition, so merging it can't do any of the things above. Everything
downstream of that (picking an entry, running `/test-paper`, spending, publishing) still
requires the human.

## Where things live

- Proposals queue: `queue.md`
- Scout sources (editable): `.claude/scout/sources.yaml`
- Subagents: `.claude/agents/research-scout.md`, `.claude/agents/skill-scout.md`
- Invoke the scouts: `/scout-research`, `/scout-skills`
- Experiment command: `/test-paper`  ·  Scoreboard: the table in `README.md`
- Auto-merge gate for scout PRs: `.github/workflows/validate-scout-pr.yml`

## Scheduling

`/scout-research` runs on a scheduled routine wrapping the command — no changes to the agent
were needed. Each run opens a PR that auto-merges once `validate-scout-pr` passes (see above),
so `queue.md` stays current without a human clicking merge on every run; picking an entry to
test is still entirely on the human.
