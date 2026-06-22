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

## Scheduling (later, not now)

The research scout is manual on purpose. To automate it later, wrap `/scout-research` in a
scheduled routine — no changes to the agent are needed. No scheduler is set up yet.
