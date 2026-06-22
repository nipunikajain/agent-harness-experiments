Run the research scout.

Use the research-scout subagent to find new research in my lane (AI agents, MCP, agent
harnesses & infrastructure, LLM systems & serving). It must:

- read its sources from `.claude/scout/sources.yaml`,
- dedupe against the README scoreboard and `queue.md` (creating `queue.md` if missing),
- append a ranked shortlist of new candidates to `queue.md`, each marked
  `proposed — awaiting review`, with title+link, one-line claim, why it matters, and a
  testability read (small-model/hardware feasibility + rough cost),
- then stop.

It proposes only: never install anything, never run /test-paper, never start an experiment.

$ARGUMENTS

When it returns, show me a one-line summary (how many added + their titles) and remind me that
I decide what, if anything, to run.
