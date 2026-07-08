# Discovery queue

Proposals from the research scout. Nothing here runs automatically — you pick an entry, then
run `/test-paper <link>` yourself. Update Status as you go.

Status legend: proposed (awaiting your review) · queued (approved, not yet run) · testing ·
done (in the README scoreboard) · rejected.

<!-- The research-scout subagent appends one dated `## <date> — proposed by research-scout`
     section per run below this line. It dedupes against this file and the README scoreboard,
     so already-tested or already-queued items are never resurfaced. -->

---

## 2026-07-07 — proposed by research-scout

### [Self-Harness: Harnesses That Improve Themselves](https://arxiv.org/abs/2606.09498)
- Status: proposed — awaiting review
- Claim: An agent that iteratively mines its own failure traces, proposes minimal harness edits, and validates them via regression testing (Weakness Mining → Harness Proposal → Proposal Validation) lifts held-out Terminal-Bench-2.0 pass rates for 3 base models: 40.5%→61.9%, 23.8%→38.1%, 42.9%→57.1%.
- Why it matters: Directly extends this repo's existing harness-overhead findings (all 3 scoreboard rows show hand-designed structured harnesses losing to naive) — this asks whether a *self-editing* harness can actually earn its keep instead of costing tokens for nothing.
- Testability: Feasible small-scale. Build a toy multi-task suite (not full Terminal-Bench) and run the 3-stage loop with Haiku 4.5 as both agent and harness-editor; Sonnet 4.6 as judge/validator. Pure API calls, no GPU. Rough cost: $10-20 for enough iterations across a handful of seeds to see a trend — fits the $25/experiment budget, though full Terminal-Bench-2.0 replication would not.
- Source: arXiv cs.AI (2606.09498)

### [Less Context, Better Agents: Efficient Context Engineering for Long-Horizon Tool-Using LLM Agents](https://arxiv.org/abs/2606.10209)
- Status: proposed — awaiting review
- Claim: On a 50-task hotel-expense benchmark using MCP tools, going from no user-model to full conversation history raises task completion from 8.0% to 71.0% but costs 1.48M tokens / 14.56 hours; the paper argues pruned/summarized context can recover most of the completion rate for a fraction of the tokens (4 configs compared: no-model, full-history, last-5-pruned, pruned+summarized).
- Why it matters: A concrete, cheap-to-replicate MCP-tool-response-bloat problem — distinct from the session/state-structuring harness already tested here; this is about pruning verbose tool outputs, not per-session task scaffolding.
- Testability: Very feasible on Apple Silicon/API only. Build a small (~15-20 task) tool-use benchmark with an MCP-style verbose tool, run the same 4 context configs with Haiku 4.5 or Sonnet 4.6. No GPU needed. Rough cost: $5-15 in API calls.
- Source: arXiv cs.CL/cs.AI (2606.10209)

### [Breaking the Protocol: Security Analysis of the Model Context Protocol Specification and Prompt Injection Vulnerabilities in Tool-Integrated LLM Agents](https://arxiv.org/abs/2601.17549)
- Status: proposed — awaiting review
- Claim: Across 847 controlled attack scenarios on 5 MCP server implementations, MCP's architectural choices (no capability attestation, unauthenticated bidirectional sampling, implicit multi-server trust) amplify prompt-injection attack success rates by 23-41% vs. equivalent non-MCP tool integrations; a proposed "MCPSec" extension cuts success from 52.8% to 12.4%.
- Why it matters: Concrete, falsifiable security claim directly about MCP infrastructure — this repo's lane includes MCP explicitly, and a directional replication (does routing the same attack through MCP vs. a plain function-call harness really change success rate?) is a natural fit.
- Testability: Cheap and GPU-free. Build one minimal mock MCP server and one equivalent non-MCP tool harness, run a reduced attack set (~50-100 scenarios, not 847) against Haiku 4.5 and/or Sonnet 4.6, compare success rates. Rough cost: $5-10 in API calls.
- Source: arXiv cs.CR/cs.AI (2601.17549)

### [ARC: Active and Reflection-driven Context Management for Long-Horizon Information Seeking Agents](https://arxiv.org/abs/2601.12030)
- Status: proposed — awaiting review
- Claim: Treating context as a dynamic, reflection-revised reasoning state (vs. passive accumulation/summarization) yields up to +11 points absolute accuracy on BrowseComp-ZH with Qwen2.5-32B-Instruct, with gains amplifying on harder/longer tasks; benefits weaker models more than strong ones.
- Why it matters: A different context-management mechanism (active reflection/reorganization, not just pruning) for long-horizon agents — complements the harness-overhead results already on the scoreboard and the other context-engineering candidates above without duplicating them.
- Testability: Feasible on a small model. Implement a lightweight reflection-driven context reorganizer on top of a toy long-horizon search/QA task, compare vs. ReAct and vs. plain summarization using Haiku 4.5. No GPU required. Rough cost: $10-15 in API calls; won't reproduce their exact benchmark/model scale, only the directional effect.
- Source: arXiv cs.CL/cs.AI (2601.12030)

### [GenericAgent: A Token-Efficient Self-Evolving LLM Agent via Contextual Information Density Maximization (V1.0)](https://arxiv.org/abs/2604.17091)
- Claim: A minimal atomic tool set + hierarchical on-demand memory + self-evolution (turning verified trajectories into reusable SOPs/code) + context truncation reportedly cuts token consumption by nearly 90% while staying within a 30k-token context, on general long-horizon agent tasks.
- Status: proposed — awaiting review
- Why it matters: A concrete "context density" alternative to this repo's already-tested "1-feature/session" structuring — worth checking whether the token savings are real or (like the tested structured harness) come at a hidden quality cost.
- Testability: Feasible small-model repro. Implement the 4 components in a toy long-horizon coding/tool task, compare token usage and task success vs. a naive baseline using Haiku 4.5, CPU/API only. Rough cost: $10-20; the "self-evolution into reusable SOPs" part may need a few extra episodes to show any effect, but stays within budget.
- Source: arXiv cs.AI (2604.17091)

### [TokenPilot: Cache-Efficient Context Management for LLM Agents](https://arxiv.org/abs/2606.17016)
- Status: proposed — awaiting review
- Claim: Ingestion-Aware Compaction (stabilize prompt prefixes) + Lifecycle-Aware Eviction (offload stale context on a conservative schedule) cuts inference cost by 61%/56% (isolated mode) and 61%/87% (continuous mode) on two agent benchmarks (PinchBench, Claw-Eval) vs. prior context-management systems, while holding task performance roughly constant.
- Why it matters: Tests whether prefix-stability-aware pruning (using vendor prompt caching, e.g. Anthropic's cache_control) actually beats naive pruning on real cost, not just token count — a different, infra-adjacent angle from the other context-engineering candidates.
- Testability: Feasible without GPU. Reproduce directionally using Claude's prompt-caching API on Haiku 4.5/Sonnet 4.6 with a small toy agent benchmark, measuring actual billed cost (cache hits/misses) rather than raw token count. Rough cost: $10-15. Full PinchBench/Claw-Eval scale is out of scope for a $25 budget; this would be a small directional check.
- Source: arXiv cs.DC/cs.CL (2606.17016)
