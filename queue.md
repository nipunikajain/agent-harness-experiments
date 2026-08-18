# Discovery queue

Proposals from the research scout. Nothing here runs automatically — you pick an entry, then
run `/test-paper <link>` yourself. Update Status as you go.

Status legend: proposed (awaiting your review) · queued (approved, not yet run) · testing ·
done (in the README scoreboard) · rejected.

<!-- The research-scout subagent appends one dated `## <date> — proposed by research-scout`
     section per run below this line. It dedupes against this file and the README scoreboard,
     so already-tested or already-queued items are never resurfaced. -->

<!-- 2026-08-16: consolidated 13 backlogged scout-run PRs (#3, #6-#17) that had accumulated
     unmerged, each branched from the same base and blind to the others' additions. Merged
     here in run-date order; 29 cross-run duplicate proposals (same underlying paper/post,
     sometimes with a different title/wording) were dropped, keeping the earliest occurrence
     of each. Nothing else changed — every surviving entry is still proposed — awaiting review. -->

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

---

## 2026-07-08 — proposed by research-scout

### [When Agents Do Not Stop: Uncovering Infinite Agentic Loops in LLM Agents](https://arxiv.org/abs/2607.01641)
- Status: proposed — awaiting review
- Claim: Static analysis tool (IAL-Scan) that builds an "Agentic Loop Dependence Graph" over agent code, scanning 6,549 real LLM agent repos and confirming 68 "Infinite Agentic Loop" failures (unbounded model-call/tool/handoff feedback paths that cause cost exhaustion or DoS) across 47 projects at 91.9% precision.
- Why it matters: This repo's harness experiments already probe cost/overhead failure modes of agent scaffolding — IALs are a distinct, concrete "runaway cost" failure class worth checking whether a naive vs. structured harness is more/less prone to it, directly relevant to the agent-harness lane.
- Testability: Feasible on Apple Silicon/API only. Don't need the full static-analysis tool — build a handful of toy agent harnesses (naive loop, ReAct, subagent handoff) with deliberately weak termination conditions, run them against Haiku 4.5 with a hard step/cost cap, and count how often each pattern actually runs away vs. terminates cleanly. Rough cost: $5-10, since runaway runs must be capped tightly to stay in budget.
- Source: arXiv cs.SE/cs.AI (2607.01641), submitted 2026-07-02

### [Recursive Agent Harnesses](https://arxiv.org/abs/2606.13643)
- Status: proposed — awaiting review
- Claim: Frames "harness recursion" — a parent agent that generates and runs an executable script spawning full subagent harnesses (with their own filesystem tools, code execution, and planning) in parallel, rather than plain recursive model calls (RLMs) — and provides a controlled long-context-reasoning evaluation of the pattern.
- Why it matters: A different self-similar-harness mechanism than Self-Harness (queued 07-07, which self-*edits*) or the tested 1-feature/session structuring on the scoreboard — this is about spawning full recursive subagent harnesses for parallel subtasks, worth checking whether it earns back its overhead the way the existing scoreboard rows failed to.
- Testability: Feasible small-scale. Build a toy long-context task solvable by (a) a single flat agent and (b) a parent agent that spawns 2-3 subagent harnesses in parallel via generated scripts, using Haiku 4.5 for subagents and Sonnet 4.6 as parent/judge. No GPU. Rough cost: $10-15; won't match their long-context scale but can test the directional cost/quality tradeoff.
- Source: arXiv cs.CL (2606.13643), submitted 2026-06-11

### [PlanBench-XL: Evaluating Long-Horizon Planning of LLM Tool-Use Agents in Large-Scale Tool Ecosystems](https://arxiv.org/abs/2606.22388)
- Status: proposed — awaiting review
- Claim: New benchmark (327 retail tasks, 1,665 tools) with a blocking mechanism simulating missing/failing/distracting tools; GPT-5.4 scores 51.90% accuracy block-free but collapses to 11.36% under the most severe blocking, showing tool-retrieval-limited planning degrades sharply when tools are unreliable.
- Why it matters: Directly tests tool-use robustness under realistic MCP-style tool ecosystems (large tool count, partial failures) — a different angle from the context-pruning/MCP-security candidates already queued, closer to "does the agent's plan survive a flaky tool registry."
- Testability: Feasible on API only. Build a small (~20-30 task) tool-use benchmark with a large-ish synthetic tool registry and an injectable blocking/failure rate, run Haiku 4.5 and Sonnet 4.6 across block-free vs. blocked conditions. No GPU. Rough cost: $10-15; full 1,665-tool/327-task scale is out of budget, this would be a smaller directional check of the same collapse pattern.
- Source: arXiv cs.AI (2606.22388), submitted 2026-06-21

### [Your Agent's Memories Are Not Its Own: Forged Reasoning Attacks on LLM Agent Memory and Defenses](https://arxiv.org/abs/2607.05029)
- Status: proposed — awaiting review
- Claim: Introduces FARMA, an attack that poisons an agent's persistent *reasoning* memory (not factual knowledge) with forged rationale traces using evasive language that bypasses keyword filters and self-referential reinforcement that defeats consensus-based defenses; proposes SENTINEL, a layered defense pipeline, as a countermeasure.
- Why it matters: A different security angle from the queued MCPSec candidate (protocol-level prompt injection) — this targets agent memory/reasoning-trace poisoning specifically, relevant if any future harness experiment here adds persistent memory across sessions.
- Testability: Feasible without GPU. Build a toy agent with a simple persistent memory store, attempt a scaled-down forged-reasoning injection over a handful of sessions with Haiku 4.5/Sonnet 4.6, measure attack success rate with and without a simplified SENTINEL-style filter. Rough cost: $10-15; won't replicate their full attack suite, only the directional "does forged reasoning propagate and can a simple defense catch it" check.
- Source: arXiv cs.CR/cs.AI (2607.05029), submitted 2026-07-06

### [Can I Buy Your KV Cache?](https://arxiv.org/abs/2606.13361)
- Status: proposed — awaiting review
- Claim: Precomputed KV caches can be shared/reused across agents reading the same document — loading a precomputed KV and continuing generation is token-exact with prefilling from scratch (24/24 greedy tokens match, logit-level match), and on Qwen3-4B reuse is 9-50x cheaper in compute than prefill, with the advantage growing with document length.
- Why it matters: A concrete, falsifiable serving/infra claim in the LLM-serving lane — distinct from the agent-context-caching angle of queued TokenPilot, this is about literally reusing a precomputed KV cache across separate inference calls/agents rather than prompt-prefix caching within one session.
- Testability: Needs a local/open-weight model to inspect and reuse raw KV tensors (not available through the Claude API) — out of scope for CPU-only Apple Silicon at any real scale. A small open model (e.g. a 1-4B model) could run on Modal GPU to verify token-exact reuse and measure prefill-time savings directly. Rough Modal cost: a single small GPU (T4/A10G) for a few hours of experimentation, likely $10-20 — fits the $25 budget if scoped to one small model and a handful of documents, but is a GPU-required experiment, not a CPU/API-only one.
- Source: arXiv cs.DC/cs.LG (2606.13361), submitted 2026-06-13

### [KARA: Efficient Reasoning LLM Serving via Sliding-Window KV Cache Compression](https://arxiv.org/abs/2607.01237)
- Status: proposed — awaiting review
- Claim: Decoding-time sliding-window KV cache compression (with bidirectional-attention scoring and a Token2Chunk module to preserve chunk-level semantics) integrated into a vLLM-based framework (KvLLM) improves serving throughput for reasoning LLMs while preserving accuracy — e.g. near-unchanged accuracy on MATH-500 with Qwen3-14B at a 30% KV retention ratio.
- Why it matters: A serving-infra KV-cache-compression claim distinct from the queued "Can I Buy Your KV Cache?" (cache *reuse* across calls) — this is about compressing/evicting KV during a single long reasoning generation, testable directly against the vLLM blog's own lane.
- Testability: Needs a GPU and vLLM — not feasible on CPU-only Apple Silicon. Could run a small open reasoning model (e.g. a 1.5B-7B class model) on a Modal A10G, comparing vanilla vLLM KV cache vs. a simplified sliding-window compression at a couple of retention ratios on a small math-reasoning eval subset. Rough Modal cost: $15-25 for a few hours of A10G time — near the top of the per-experiment budget; would need to be scoped tightly (small model, small eval set) to fit.
- Source: arXiv cs.DC/cs.CL (2607.01237), submitted 2026-07-01

---

## 2026-07-10 — proposed by research-scout

### [Stop Comparing LLM Agents Without Disclosing the Harness](https://arxiv.org/abs/2605.23950)
- Status: proposed — awaiting review
- Claim: Position paper + controlled variance decomposition arguing that for long-horizon agent tasks, harness-induced performance variance (context construction, tool interaction, orchestration, verification) can exceed model-induced variance — including cases of model-ranking reversal — so current benchmarks systematically misattribute harness gains to model improvements.
- Why it matters: This is the closest thing to a direct meta-validation of this repo's own thesis — all three existing scoreboard rows already show harness choice dominating or nullifying model-level effects. Worth checking whether their variance-decomposition protocol, applied to this repo's own existing results, reproduces the "harness variance > model variance" pattern, and whether one new controlled run confirms it on a fresh task.
- Testability: Very cheap. Much of this could be a re-analysis of already-collected scoreboard data (naive vs. structured harness × Haiku vs. Sonnet) using their variance-decomposition framing, plus one small new 2-harness × 2-model run on a fresh toy task to check for ranking reversal. No GPU. Rough cost: $5-10 in API calls for the new run; analysis of existing data is free.
- Source: arXiv cs.AI (2605.23950)

### [Harness Updating Is Not Harness Benefit: Disentangling Evolution Capabilities in Self-Evolving LLM Agents](https://arxiv.org/abs/2605.30621)
- Status: proposed — awaiting review
- Claim: Splits self-evolving-harness ability into two components — "harness-updating" (producing useful persistent harness edits) and "harness-benefit" (benefiting from those edits during task-solving) — and finds harness-updating is roughly flat across model capability tiers (even Qwen3.5-9B's edits rival Claude Opus 4.6's), while harness-benefit is non-monotonic: weak models barely benefit, mid-tier models benefit most, strong models benefit less than mid-tier.
- Why it matters: Directly extends this repo's own DB-harness result (Haiku vs. Sonnet diverged sharply on whether structuring helped) with a cleaner mechanism — separating "who writes the harness update" from "who benefits from it." Cheap to check with the same Haiku/Sonnet pairing already used on the scoreboard.
- Testability: Feasible small-scale. Build a toy multi-task suite with a self-evolution loop; use Haiku 4.5 as the weak/evolver tier and Sonnet 4.6 as the mid/strong tier (no Opus access needed to see the non-monotonic trend directionally), cross harness-updater and harness-benefiter roles. Pure API, no GPU. Rough cost: $10-15.
- Source: arXiv cs.AI (2605.30621)

### [TencentDB-Agent-Memory](https://github.com/TencentCloud/TencentDB-Agent-Memory)
- Status: proposed — awaiting review
- Claim: A layered, symbolized agent-memory plugin (symbolic short-term memory that condenses tool logs into compact "Mermaid symbols" + layered long-term memory distilling conversations into structured personas/scenes) reports, vs. baseline without the plugin: WideSearch success 33%→50% (−61% tokens), SWE-bench 58.4%→64.2% (−33% tokens), PersonaMem accuracy 48%→76%.
- Why it matters: A concrete, numbers-attached long-horizon-memory claim in the agent-harness lane, using a local SQLite + sqlite-vec backend with no required external API dependency for storage — directly testable against this repo's existing long-horizon/context-management findings (TokenPilot, GenericAgent already queued/tested).
- Testability: Very feasible on Apple Silicon. Local SQLite backend, only the LLM calls hit an API (Haiku 4.5/Sonnet 4.6); build a small multi-session long-horizon task and compare with/without the memory plugin. No GPU needed. Rough cost: $5-10 in API calls; full WideSearch/SWE-bench scale is out of budget, this would be a small directional check.
- Source: GitHub trending (python/agents)

### [Bridging Protocol and Production: Design Patterns for Deploying AI Agents with Model Context Protocol](https://arxiv.org/abs/2603.13417)
- Status: proposed — awaiting review
- Claim: Identifies 3 missing MCP primitives from field experience at enterprise scale (identity propagation, adaptive tool budgeting, structured error semantics) and proposes fixes: a Context-Aware Broker Protocol (CABP) for identity-scoped routing, Adaptive Timeout Budget Allocation (ATBA) for sequential tool-call budgeting, and a Structured Error Recovery Framework (SERF).
- Why it matters: A production-infra angle on MCP distinct from the already-queued MCP security papers — asks whether adaptive timeout/error-recovery patterns actually reduce task failure under a flaky multi-tool MCP setup, complementing the queued PlanBench-XL "flaky tool registry" candidate from a design-pattern (not benchmark) angle.
- Testability: Feasible on API only. Build a small mock MCP server with injectable latency/timeouts and errors, compare a fixed-timeout/naive-retry baseline vs. a simplified ATBA+SERF implementation on task completion rate, using Haiku 4.5/Sonnet 4.6. No GPU. Rough cost: $10-15; the paper's claims are mostly qualitative field lessons rather than a single number, so this would be a directional "does the pattern help" check, not a tight replication.
- Source: arXiv cs.SE/cs.DC (2603.13417), submitted 2026-03-12

### [MCP-DPT: A Defense-Placement Taxonomy and Coverage Analysis for Model Context Protocol Security](https://arxiv.org/abs/2604.07551)
- Status: proposed — awaiting review
- Claim: Introduces a layer-aligned taxonomy organizing MCP attacks by which architectural component (client, server, broker, LLM) should be responsible for enforcing the corresponding defense, arguing existing attack-centric/benchmark-driven work gives limited guidance on defense placement.
- Why it matters: Complements the already-queued MCP security paper ("Breaking the Protocol," which measures raw attack success rates) with a placement question — does moving the *same* defense to a different architectural layer change its effectiveness? A natural, cheap follow-on using the same mock-MCP-server setup already proposed for that candidate.
- Testability: Cheap and GPU-free. Reuse a minimal mock MCP server + a reduced attack set (~20-30 scenarios), implement the same defense (e.g. an injection filter) at 2-3 different taxonomy-suggested layers, and compare coverage. Rough cost: $5-10 in API calls with Haiku 4.5/Sonnet 4.6.
- Source: arXiv cs.CR (2604.07551), submitted 2026-04-08

### [DSpark: Confidence-Scheduled Speculative Decoding with Semi-Autoregressive Generation](https://arxiv.org/abs/2607.05147)
- Status: proposed — awaiting review
- Claim: A semi-autoregressive drafter (parallel backbone + lightweight sequential module for intra-block dependency modeling) plus confidence-scheduled, load-aware verification length substantially improves accepted length over prior autoregressive/parallel drafters; in DeepSeek-V4 production serving, accelerates per-user generation 60-85% vs. the MTP-1 baseline at matched throughput.
- Why it matters: A serving/inference-optimization claim squarely in the LLM-serving lane (KV cache/speculative decoding), distinct from the already-queued KV-cache candidates — tests decoding-side throughput rather than cache reuse/compression.
- Testability: Needs a GPU and an open-weight model with an available draft/target pair (not reproducible through the Claude API) — out of scope for CPU-only Apple Silicon. A small open model (e.g. 1-3B target + small draft) on a Modal GPU could verify the directional accepted-length improvement of confidence-scheduled vs. fixed-length verification on a small eval set. Rough Modal cost: $15-25 for a few hours of A10G time — near the top of the per-experiment budget, would need tight scoping (small models, small eval).
- Source: arXiv cs.CL/cs.DC (2607.05147), submitted 2026-07-06

### [Harness as an Asset: Enforcing Determinism via the Convergent AI Agent Framework (CAAF)](https://arxiv.org/abs/2604.17025)
- Status: proposed — awaiting review
- Claim: Proposes a closed-loop, fail-safe-deterministic orchestration framework (Recursive Atomic Decomposition with context firewalls, domain invariants formalized as an executable/enforced "Harness as an Asset" registry, and structured semantic gradients with state locking) to close a "controllability gap" where even low rates of undetected constraint violations render a system undeployable; argues no single pillar alone suffices.
- Why it matters: A determinism/regression-prevention framing that lines up almost exactly with this repo's own DB-harness finding of "0 regressions in all 12 runs but zero measured benefit" — worth checking whether CAAF's specific mechanism (machine-readable invariant registry + deterministic assertion interface) produces a *measurable* quality or reliability gain the prior tested harness didn't, or is another overhead-only mechanism.
- Testability: Feasible but conceptual/vaguer than the other candidates — it's a framework paper, not a single benchmark number. Implement just the "Harness as an Asset" pillar (an invariant registry + deterministic checker) on a toy multi-step task with injected constraint violations, compare regression/violation rate and cost vs. a no-registry baseline, using Haiku 4.5/Sonnet 4.6. No GPU. Rough cost: $10-15; scoping to one pillar (not all three) is necessary to stay in budget and keep the comparison controlled.
- Source: arXiv cs.AI/cs.SE (2604.17025)
## 2026-07-09 — proposed by research-scout

### [Adapting the Interface, Not the Model: Runtime Harness Adaptation for Deterministic LLM Agents](https://arxiv.org/abs/2605.22166)
- Status: proposed — awaiting review
- Claim: Life-Harness converts recurring interaction failures observed during a training phase into reusable interventions across four categories (environment contracts, procedural skills, action realization, trajectory regulation), then freezes the harness for evaluation on unseen tasks — improving 116 of 126 model×environment settings across 18 model backbones on τ-bench, τ²-bench, and AgentBench, averaging +88.5% relative improvement, without changing model weights.
- Why it matters: A much larger claimed effect size than this repo's own tested "1-feature/session" structuring (which found zero benefit for real cost) — the key structural difference is "freeze after training, no further per-session overhead at eval time," which is exactly the failure mode the scoreboard rows blame for the tested harness's cost. Worth checking if freezing is the missing ingredient.
- Testability: Feasible small-scale, API only. Build a toy deterministic tool-use task (τ-bench-style), run a short "training" phase where Sonnet 4.6 mines a handful of induced failures into the four intervention categories, freeze the resulting harness, then evaluate both Haiku 4.5 and Sonnet 4.6 against a naive baseline on held-out tasks. No GPU. Rough cost: $10-20; won't match the 18-backbone/3-benchmark scale, only the directional "does freezing help" effect.
- Source: arXiv cs.AI (2605.22166), submitted 2026-05-22

### [Better Models: Worse Tools](https://simonwillison.net/2026/Jul/4/better-models-worse-tools/)
- Status: proposed — awaiting review
- Claim: Blog post (Armin Ronacher, syndicated via Simon Willison) reporting that newer Claude models (Opus 4.8, Sonnet 5) invent extra, non-schema fields when calling a third-party harness's custom edit tool (the Pi editor), a regression not present in older models — hypothesized to result from RL post-training tuned specifically to Claude Code's own edit-tool schema, which fails to generalize to other harnesses' custom tool schemas.
- Why it matters: A concrete, falsifiable claim squarely in the agent-harness lane — if newer/"better" models are quietly worse at *custom* (non-Claude-Code) tool schemas, that's a direct risk for any harness in this repo built on bespoke tools rather than Claude Code's own conventions.
- Testability: Very cheap, API only. Define two edit-tool schemas — one mirroring Claude Code's own edit-tool field conventions and one deliberately different (custom field names/structure) — run a small battery of edit tasks against current models (Haiku 4.5, Sonnet 4.6) and measure schema-violation rate on the non-standard schema. No GPU. Rough cost: $5-10.
- Source: Blog — Armin Ronacher (lucumr.pocoo.org), syndicated via Simon Willison's Weblog, published 2026-07-04

### [Enhancing Model Context Protocol (MCP) with Context-Aware Server Collaboration](https://arxiv.org/abs/2601.11595)
- Status: proposed — awaiting review
- Claim: Proposes CA-MCP, restructuring stock (stateless) MCP so the central LLM handles only high-level planning and final summarization, while a Shared Context Store accessible to all MCP servers holds global context — aiming to cut redundant computation and improve coherence in multi-server agent workflows.
- Why it matters: A distinct MCP-infrastructure angle from the already-queued MCPSec (protocol security) — this is about efficiency/coherence of multi-server MCP workflows, directly testable with a small toy multi-server setup and squarely in this repo's MCP lane.
- Testability: Feasible, API only. Build 2-3 mock MCP servers with overlapping sub-tasks, compare token usage/redundant re-fetching and end-task coherence with vs. without a simple shared context store, using Haiku 4.5 and/or Sonnet 4.6. No GPU. Rough cost: $5-10.
- Source: arXiv cs.AI/cs.DC (2601.11595), submitted 2026-01-06, revised 2026-01-22

---

## 2026-07-13 — proposed by research-scout

### [HarnessX: A Composable, Adaptive, and Evolvable Agent Harness Foundry](https://arxiv.org/abs/2606.14249)
- Status: proposed — awaiting review
- Claim: Assembling typed harness primitives via a "substitution algebra" and adapting them with AEGIS, a trace-driven multi-agent evolution engine that also feeds trajectories back as model-training signal, yields an average +14.5% (up to +44.0%) across 5 agent benchmarks (ALFWorld, GAIA, WebShop, tau³-Bench, SWE-bench Verified), with gains largest where baselines are weakest.
- Why it matters: A different self-evolving-harness mechanism than the already-queued Self-Harness (which mines failure traces → proposes edits → validates via regression testing) — HarnessX composes typed primitives algebraically and closes the loop into model-training signal too. Worth flagging the overlap explicitly: both ultimately test "can a self-editing harness earn its keep," which this repo's tested rows say hand-designed structured harnesses generally do not.
- Testability: Feasible small-scale. Implement a stripped-down primitive library (3-5 primitives: memory, tool-selection, replanning, verification) plus a simple trace-driven selection loop (skip the full AEGIS/RL machinery) on a toy task suite, Haiku 4.5 as agent, Sonnet 4.6 as evolution/judge. No GPU. Rough cost: $15-20; full 5-benchmark scale is out of budget — this would be a directional check on 1-2 toy tasks.
- Source: arXiv cs.AI/cs.CL (2606.14249), submitted 2026-06-12

### [Natural-Language Agent Harnesses](https://arxiv.org/abs/2603.25723)
- Status: proposed — awaiting review
- Claim: Harness control logic (handoffs, state updates, validation gates, artifact contracts) can be represented as an editable natural-language document (a "Natural-Language Agent Harness") interpreted at runtime by a shared "Intelligent Harness Runtime," with empirically demonstrated operational viability, interpretable module-level effects, and robust code-to-text migration — i.e. NL-harnesses behave equivalently to code-based ones while being more inspectable/portable.
- Why it matters: A representational claim about harnesses rather than a performance-optimization one — directly relevant to how this repo authors its own harnesses (currently Python `intervention.py`); tests whether describing the *exact same* structured-vs-naive harness policy as an NL document interpreted by a runtime changes behavior/cost/quality vs. the code version already on the scoreboard.
- Testability: Very cheap, API-only. Rewrite the repo's existing tested structured harness's control logic as an NL policy document, build a minimal interpreter loop, and compare token cost/task success against the already-tested code version on the same toy task. No GPU. Rough cost: $5-10 — could even reuse existing scoreboard results as one arm instead of rerunning them.
- Source: arXiv cs.AI/cs.CL (2603.25723), submitted 2026-03-26

### [AOrchestra: Automating Sub-Agent Creation for Agentic Orchestration](https://arxiv.org/abs/2602.03786)
- Status: proposed — awaiting review
- Claim: Modeling every (sub)agent as a dynamic (Instruction, Context, Tools, Model) tuple, with a non-executing orchestrator that concretizes and spawns a tailored sub-agent on demand per subtask, yields a 16.28% relative improvement over the strongest baseline (paired with Gemini-3-Flash) across GAIA, SWE-Bench, and Terminal-Bench.
- Why it matters: Distinct from the already-queued Recursive Agent Harnesses (a parent that spawns full recursive subagent harnesses via a generated script) — AOrchestra's orchestrator never executes tasks itself and dynamically selects tools/model/context per subtask rather than recursing. Worth checking whether "on-demand specialized sub-agent creation" earns back overhead the way this repo's tested harnesses have not.
- Testability: Feasible small-scale. Build a toy multi-step task solvable by (a) one flat agent and (b) an orchestrator (Sonnet 4.6) that dynamically spawns tailored sub-agents (Haiku 4.5) per subtask, compare cost and success. No GPU. Rough cost: $10-15; won't match GAIA/SWE-Bench scale, directional only.
- Source: arXiv cs.AI/cs.MA (2602.03786), submitted 2026-02-04

### [Model Context Protocol (MCP) Tool Descriptions Are Smelly!](https://arxiv.org/abs/2602.14878)
- Status: proposed — awaiting review
- Claim: Empirical study of 856 tools across 103 real MCP servers finds 97.1% of tool descriptions have at least one "smell" (56% don't state purpose clearly); augmenting descriptions to fix all identified smells improves task success by a median +5.85pp and partial-goal completion by +15.12%, but increases execution steps by 67.46% and regresses performance in 16.67% of cases.
- Why it matters: A concrete, quantified MCP-specific claim in this repo's lane — distinct from the queued MCP-security paper (attack surface) and the context-pruning candidates (verbose tool *outputs*), this is about tool *description* quality, with an explicit tradeoff (better success sometimes, but more steps and real regression risk) that's cheap to falsify.
- Testability: Very feasible, API-only. Build a small MCP-style toy server (5-10 tools) with deliberately "smelly" descriptions (missing purpose/params/examples) vs. an augmented set, run Haiku 4.5 and Sonnet 4.6 across a small task suite, measure success rate, step count, and regression rate. No GPU. Rough cost: $5-10.
- Source: arXiv cs.SE/cs.AI (2602.14878), submitted 2026-02-14

### [DemoEvolve: Overcoming Sparse Feedback in Agentic Harness Evolution with Demonstrations](https://arxiv.org/abs/2605.24539)
- Status: proposed — awaiting review
- Claim: In long-horizon, high-variance, sparse-reward stochastic environments (tested on the card games Liar's Dice and Balatro), pure self-rollout harness evolution (reward-only search) is misled by noisy/sparse feedback, but bootstrapping the harness-editing proposer with a handful of competent human demonstration trajectories produces more effective and auditable harness edits under the same limited budget.
- Why it matters: A different failure mode for self-evolving harnesses than HarnessX/Self-Harness above — specifically the sparse-feedback/high-variance regime where naive self-rollout evolution breaks down; complements this repo's own finding that structured harnesses often fail to earn back overhead, by asking whether demonstrations specifically fix that failure mode.
- Testability: Feasible small-scale. Use a small custom stochastic toy task with sparse, delayed reward (not the full Balatro/Liar's Dice games) with Haiku 4.5 as the acting agent and Sonnet 4.6 as the harness-editing proposer; compare self-rollout-only evolution vs. demonstration-bootstrapped evolution over a handful of iterations. No GPU. Rough cost: $15-20.
- Source: arXiv cs.AI/cs.LG (2605.24539), submitted 2026-05-30

### [Speculative Speculative Decoding](https://arxiv.org/abs/2603.03251)
- Status: proposed — awaiting review
- Claim: An asynchronous speculative-decoding variant that parallelizes drafting and verification — the draft model predicts likely verification outcomes and pre-generates the next speculation while the previous step's verification is still in flight, skipping drafting overhead when the prediction is right. The resulting "Saguaro" implementation is reported ~30% faster on average than optimized speculative-decoding baselines and up to 5x faster than plain autoregressive decoding on open-source inference engines.
- Why it matters: A concrete LLM-serving/inference-optimization claim (speculative decoding is explicitly in `sources.yaml`'s query terms) distinct from the KV-cache-focused candidates already queued — this is about decode-time throughput via async draft/verify overlap.
- Testability: Needs a GPU and a real inference engine (vLLM/SGLang) with an open-weight draft+target model pair — not feasible on CPU-only Apple Silicon. Could run a small pair (e.g. ~1B draft + 7-8B target) on a Modal A10G, comparing vanilla speculative decoding vs. an implemented async draft/verify overlap on a small generation benchmark. Rough Modal cost: $15-25 for a few hours of A10G — near/at the top of the per-experiment budget; would need tight scoping (small models, short benchmark) to fit.
- Source: arXiv cs.CL/cs.LG (2603.03251), submitted 2026-03-03

---

## 2026-07-16 — proposed by research-scout

### [Learning to Control LLM Agent Harnesses with Offline Reinforcement Learning](https://arxiv.org/abs/2607.05458)
- Status: proposed — awaiting review
- Claim: Formalizes harness operation as a finite-horizon "Harness MDP" where a lightweight controller (not the LLM itself, which stays frozen) selects structural execution actions (e.g. verify, retry, escalate); trained offline via advantage-weighted regression from rollouts with only terminal task-rubric rewards, it consistently improves verification behavior and selectively improves final task quality across 6 controlled domains + 2 public-benchmark adapters, beating behavior-cloning and a "Forced CHECK" (always-verify) ablation.
- Why it matters: A genuinely new mechanism in the harness lane — treating the harness itself as a learnable control layer rather than a hand-designed or self-editing one (distinct from queued Self-Harness and Recursive Agent Harnesses) — and it directly targets this repo's open question of whether *any* harness structure can earn back its overhead.
- Testability: Feasible on Apple Silicon. The controller is a small, cheap-to-train policy (e.g. logistic regression/tiny MLP trained on CPU), not the LLM; collect rollouts on a toy multi-step task via Haiku 4.5 API calls with a few structural harness actions, train the controller offline, compare vs. naive/heuristic control and a behavior-cloning baseline. No GPU needed. Rough cost: $10-15 in API calls for rollout collection; won't match the 6-domain/2-benchmark scope, only the directional "does a learned controller beat naive control" effect.
- Source: arXiv cs.AI (2607.05458), submitted 2026-07-05

### [Towards a Science of Scaling Agent Systems](https://arxiv.org/abs/2512.08296)
- Status: proposed — awaiting review
- Claim: Controlled evaluation of 180 agent-architecture configurations (5 canonical architectures × 3 LLM families × 4 benchmarks) finds independent multi-agent systems (parallel, no cross-checking) amplify errors 17.2×, vs. 4.4× for centralized (orchestrator-mediated) systems; more agents alone hits a ceiling or degrades performance, and a predictive model (R²=0.513, using task properties like tool count/decomposability) picks the best architecture 87% of the time on held-out tasks.
- Why it matters: A large-scale, quantitative version of exactly what this repo's scoreboard has been probing informally (does more harness/orchestration structure help or just add overhead) — but on the multi-agent-topology axis rather than session-structuring. Surfaced via a 2026 Google Research blog post; the paper itself is from December 2025 but is not close to anything already queued or tested here.
- Testability: Feasible small-scale, API only. Build a small toy task set at 2-3 decomposability levels, implement 2-3 of their architectures (single, independent-parallel, centralized-orchestrator) with Haiku 4.5/Sonnet 4.6, measure error-amplification factor and cost per architecture. No GPU. Rough cost: $10-20; won't match the 180-config/4-benchmark scale, only a directional check of "does centralized orchestration contain errors better than independent parallel agents."
- Source: arXiv cs.AI (2512.08296), submitted 2025-12; surfaced via Google Research blog, July 2026

### [The Illusion of Multi-Agent Advantage](https://arxiv.org/abs/2606.13003)
- Claim: A rigorous audit of 6 automatic multi-agent-system (MAS) design frameworks (DyLAN, MAS-Zero, AFlow, ADAS, MaAS, MAS-Orchestra) finds they consistently underperform a plain single-agent Chain-of-Thought-with-Self-Consistency (CoT-SC) baseline on both traditional reasoning benchmarks and interactive multi-step tasks (e.g. BrowseComp-Plus), despite costing up to 10× more.
- Status: proposed — awaiting review
- Why it matters: A direct, model-agnostic parallel to this repo's own findings that structured harnesses cost more for no quality gain — but on the multi-agent axis instead of session-structuring, and complements (rather than duplicates) the queued/scoreboard results and the "Scaling Agent Systems" candidate above.
- Testability: Very feasible, API only. Implement 1-2 simple auto-MAS patterns (e.g. debate/vote, planner-worker) vs. plain CoT-SC single-agent using Haiku 4.5 and/or Sonnet 4.6 on a toy reasoning benchmark, compare accuracy and cost. No GPU. Rough cost: $10-15.
- Source: arXiv cs.AI/cs.CL (2606.13003), submitted 2026-06-15

### [The Harness Effect: How Orchestration Design Sets the Token Economics of Enterprise Agentic AI](https://arxiv.org/abs/2607.06906)
- Status: proposed — awaiting review
- Claim: A controlled swap of only the orchestration layer (frozen conventional production loop vs. the "Writer Agent Harness") across 22 locked tasks and 6 foundation models (including Claude Sonnet 4.6) cuts blended cost/task 41% ($0.21→$0.12), median wall-clock 44% (48s→27s), and tokens/task 38% (14.2k→8.8k), at parity task-completion quality — every model tested improved 33-61% in cost.
- Why it matters: A rare *positive* harness-benefit claim (vendor-authored, Writer AI) directly opposed to this repo's own 3 scoreboard rows, which all found structured harnesses costing more for no quality gain. A natural adversarial check: does a differently-designed orchestration layer actually achieve what this repo's tested harnesses did not, or does it not replicate outside the vendor's own eval set?
- Testability: Feasible, API only. Build a small locked task set (~10-15 tasks), implement a simplified version of the claimed orchestration improvements (turn/tool-payload/context trimming) vs. a naive frozen-loop baseline, using Sonnet 4.6 and/or Haiku 4.5, measure cost/latency/quality. No GPU. Rough cost: $10-15.
- Source: arXiv cs.AI (2607.06906), submitted 2026-07-08

### [MemSyco-Bench: Benchmarking Sycophancy in Agent Memory](https://arxiv.org/abs/2607.01071)
- Status: proposed — awaiting review
- Claim: New 5-task benchmark for memory-induced sycophancy finds existing agent-memory systems often cause agents to over-align with retrieved memory at the cost of factual/objective accuracy — failing to reject invalid memory as evidence, respect its applicable scope, or correctly resolve conflicts between memory and fresh objective evidence.
- Why it matters: A distinct memory-failure mode from anything already queued — not an adversarial poisoning attack (FARMA/SENTINEL, already queued) and not a quality/efficiency claim (TencentDB-Agent-Memory, already queued), but a systemic bias where *legitimate* retrieved memory degrades correctness. Directly relevant to any future harness experiment here that adds persistent memory.
- Testability: Very feasible, API only. Build a small toy memory store seeded with deliberately stale/incorrect entries plus fresh contradicting evidence, run Haiku 4.5/Sonnet 4.6 with a simple memory-retrieval harness, measure how often the agent follows memory over correct fresh evidence. No GPU. Rough cost: $5-10.
- Source: arXiv cs.CL/cs.AI (2607.01071), submitted 2026-07-01

### [VeriCache: Turning Lossy KV Cache into Lossless LLM Inference](https://arxiv.org/abs/2605.17613)
- Status: proposed — awaiting review
- Claim: Uses a compressed KV cache to speculatively draft tokens, then verifies them against the full KV cache (kept off-GPU until verification) — guaranteeing output identical to full-KV decoding while achieving up to 4× higher throughput on long-context decoding and 2× on remote prefix caching, addressing the finding that lossy KV compression causes catastrophic failures in code generation and tool calling as generation lengthens.
- Why it matters: A distinct KV-cache mechanism from the two already queued (reuse across calls in "Can I Buy Your KV Cache?"; sliding-window decode-time compression in KARA) — this specifically targets the failure mode of lossy KV compression breaking tool-calling/code-gen correctness, directly relevant to any agent harness relying on KV compression for cost savings.
- Testability: Needs raw KV-cache access on an open-weight model — not reproducible via the Claude API, out of scope for CPU-only Apple Silicon. A small open model (e.g. 1-4B) on a Modal A10G GPU could verify the core draft-then-verify mechanism (token-exact match) and measure throughput on a handful of long-context/tool-calling prompts. Rough Modal cost: $15-25 for a few hours of A10G time — near/at the top of the per-experiment budget; would need tight scoping (small model, small prompt set) to fit.
- Source: arXiv cs.DC/cs.LG (2605.17613), submitted 2026-05-17

---

## 2026-07-20 — proposed by research-scout

### [AgentAbstain: Do LLM Agents Know When Not to Act?](https://arxiv.org/abs/2607.10059)
- Status: proposed — awaiting review
- Claim: First systematic benchmark for agentic abstention — 263 paired should-act/should-abstain tasks across 42 executable sandbox environments (8 abstention-scenario types). Across 17 frontier LLMs in 4 agent harnesses, the best agent (Gemini 3.1 Pro) reaches only 59.5% paired accuracy; abstention capability is largely independent of general task-solving capability, and a "post-hoc abstention" failure mode is common (agent executes an irreversible action, then only afterward recognizes it should have abstained).
- Why it matters: A harness-level safety/reliability axis distinct from every cost/quality-overhead result already on the scoreboard — this is about whether a harness lets the agent recognize when *not* to act (under ambiguity, conflicting constraints, or tool failure), directly relevant to any future harness here with tool calls, and a natural pairing with the already-queued MCP tool-failure candidates.
- Testability: Feasible on Haiku 4.5 / Sonnet 4.6 via API, no GPU. Build a small (10-20 pair) should-act/should-abstain toy suite over 1-2 sandboxed tool environments, measure paired accuracy and check for post-hoc-abstention failures across both models with 1-2 harness variants. Rough cost: $10-15; the full 263-task/42-env/17-model sweep is out of budget — this would be a small directional check.
- Source: arXiv cs.AI (2607.10059), submitted 2026-07-10

### [Set-shifting Behavioral Test for Harnessed Agents](https://arxiv.org/abs/2607.13396)
- Status: proposed — awaiting review
- Claim: Borrows "set-shifting" from cognitive psychology to test what happens when the reliable tool in a redundant tool-skill library silently changes mid-session (branched reliability schedule with hidden boundaries, paired with no-shift controls). Finds agents default to a small recurring tool-selection routine within a few turns of each boundary and often fail to fully re-adapt after a silent reliability shift, measured via a "set-shifting accuracy" score.
- Why it matters: A different tool-reliability robustness angle from the already-queued PlanBench-XL (which announces tool failure via blocking/errors) — here nothing signals the change, so it tests whether agents get stuck in a routine rather than whether they can react to an explicit error. Complements the queued AgentCheck/Bridging-Protocol/MCP-DPT tool-failure thread from a behavioral-inertia angle.
- Testability: Very feasible on Haiku 4.5 / Sonnet 4.6, API-only. Build 3-5 redundant toy tools with swappable hidden reliability, run a small task loop with a couple of silent reliability-shift boundaries plus no-shift controls, measure set-shifting accuracy. No GPU. Rough cost: $5-10.
- Source: arXiv cs.AI (2607.13396), submitted 2026-07-15

### [Self-Evolving Agent Harnesses via Gated Semantic Quality-Diversity](https://arxiv.org/abs/2607.13683)
- Status: proposed — awaiting review
- Claim: Proposes GSME, a self-evolving-harness framework that separates *proposing* edits (an LLM diagnoses failures and drafts patches) from *crediting* them (deterministic sampling, measurement, and paired significance testing on a sealed held-out test, gated by a validity gate and an activation gate), organizing credited edits into a categorical MAP-Elites quality-diversity archive — aimed squarely at preventing noisy self-generated feedback or overfitting from being mistaken for a real harness improvement.
- Why it matters: Lines up almost exactly with this repo's own experience — all 3 scoreboard rows show a "designed to help" structured harness costing more tokens for zero or negative measured benefit. GSME's validity-gating machinery is precisely the statistical discipline that could tell a real self-evolution gain from a measurement artifact, and could be applied to sanity-check the already-queued Self-Harness (07-07) candidate before it's ever run.
- Testability: Feasible small-scale, API-only. Implement just the validity-gate + paired-significance-testing core (skip the full MAP-Elites archive) on a toy multi-task suite, comparing "credited" vs. "raw" self-proposed edits, using Haiku 4.5 as proposer and a held-out seed split for sealed-test crediting. No GPU. Rough cost: $10-15.
- Source: arXiv cs.AI (2607.13683), submitted 2026-07-15

### [AgentCheck: A Reproduce-Intervene-Mitigate Workbench for LLM Agents over MCP](https://arxiv.org/abs/2607.11098)
- Claim: Open-source browser workbench that turns an MCP server into a controlled fault-injection surface — runs an agent against real tools, records every tool response, then replays with a perturbed fault (12 fault types: timeouts, stale data, poisoned descriptions, etc.) from cache while later calls go live once the agent's behavior diverges, giving a reproduce → toggle-mitigation → confirm loop. Across 120 scenarios and 5 agents, silent data-quality failures are the dominant failure category.
- Status: proposed — awaiting review
- Why it matters: A concrete, reusable fault-injection *methodology* (not just a benchmark number) for the MCP tool-failure-robustness thread already building in this queue (PlanBench-XL, Bridging Protocol's CABP/ATBA/SERF, MCP-DPT) — offers an actual harness design this repo could adapt rather than build a fault injector from scratch.
- Testability: Feasible, API-only, GPU-free — the tool itself is open-source and free to run. Point a scaled-down version at a mock MCP server with a handful of the 12 fault types, run Haiku 4.5/Sonnet 4.6 through the reproduce-intervene-confirm loop on ~10-20 scenarios. Rough cost: $5-10; the full 120-scenario/5-agent sweep is optional beyond that.
- Source: arXiv cs.AI/cs.SE (2607.11098), submitted 2026-07-11

### [Remember When It Matters: Proactive Memory Agent for Long-Horizon Agents](https://arxiv.org/abs/2607.08716)
- Status: proposed — awaiting review
- Claim: A separate memory agent runs alongside an unmodified action agent, watching for "behavioral state decay" (decision-relevant state buried in or pushed out of the context window) and deciding whether to proactively inject a memory-grounded reminder or stay silent — rather than passive retrieval-on-demand. Improves pass@1 for both weaker and stronger action agents: +8.3pp on Terminal-Bench, +6.8pp on τ²-Bench.
- Why it matters: A different memory-intervention mechanism from the already-queued TencentDB-Agent-Memory (persistent symbolic store) and ARC (reflection-driven context reorganization) — this is about *when* to actively intervene rather than *what* to store, complementary to this repo's long-horizon-agent/context-management thread without duplicating it.
- Testability: Feasible on Haiku 4.5 / Sonnet 4.6, API-only. Build a toy long-horizon multi-step task with induced "state decay" (relevant facts pushed out of the window), compare action-agent-alone vs. action+proactive-memory-agent pair on pass@1. No GPU. Rough cost: $10-15.
- Source: arXiv cs.AI/cs.CL (2607.08716), submitted 2026-07-09

### [Measuring Harness-Induced Belief Divergence in Multi-Step LLM Agents](https://arxiv.org/abs/2607.04528)
- Status: proposed — awaiting review
- Claim: Introduces a belief-rollout diagnostic (structured K-step beliefs over progress, risk, recoverability, constraints, failure mode, uncertainty, future success, repair cost, next action) and a cross-harness belief-divergence metric, decomposed into an "arrival" term (immediate interface shifts) and a "growth" term (horizon-dependent change). Shows harness variations (blocked actions, compressed repairs, selective verification, cost-aware evidence pruning) often preserve terminal task success while quietly changing the beliefs driving later decisions — i.e. harness design is an experimental variable, not an implementation detail. Open-source code provided.
- Why it matters: A concrete, open-source measurement tool for exactly the phenomenon the already-queued "Stop Comparing LLM Agents Without Disclosing the Harness" position paper argues for in the abstract — this gives an actual diagnostic (belief-rollout + a "Belief-Invariant World-Modeling" protocol) that could be applied to re-analyze this repo's own 3 scoreboard harness comparisons for *belief* divergence, not just outcome variance.
- Testability: Very cheap. Reuse this repo's own already-collected harness-comparison setups (naive vs. structured × Haiku vs. Sonnet); implement a scaled-down belief-rollout probe (a handful of belief dimensions, not all 9) at a few checkpoints per trajectory. No GPU. Rough cost: $5-10 for one small fresh run; much of the interesting analysis could reuse existing logs. Note: submitted 2026-07-04, slightly before the usual cutoff for this sweep but not previously surfaced or queued.
- Source: arXiv cs.AI/cs.CL (2607.04528), submitted 2026-07-04; code at github.com/Hik289/Harness-induce-bias

### [code-review-graph](https://github.com/tirth8205/code-review-graph)
- Status: proposed — awaiting review
- Claim: Local-first code-intelligence graph (Tree-sitter AST parsing + SQLite storage) exposed to AI coding tools via 30+ MCP tools; reports a median per-question token reduction of ~82x (range 38x-528x) across 6 real repos for code-review-relevant context retrieval vs. full-file context, with sub-2-second incremental re-indexing on repos up to ~2,900 files. The project's own docs flag some of its metrics as weak or circular (impact-analysis F1 of 0.71 is "circular by construction"; flow-detection recall only 33%).
- Why it matters: A concrete, self-reported MCP context-reduction tool with real (if self-reported and partly self-caveated) numbers — tests the context-engineering thread already in this queue (TokenPilot, GenericAgent, "Less Context, Better Agents") from a code-graph-retrieval angle rather than pruning/summarization; the tool's own honesty about weak metrics makes an independent check of its actual claims worthwhile.
- Testability: Very feasible on Apple Silicon, no GPU — it's a local SQLite-based tool; only LLM-judging calls hit the API. Index 1-2 small real repos, compare MCP-served graph context vs. naive full-file context on a handful of code-review Q&A tasks with Haiku 4.5/Sonnet 4.6, measuring both token count and answer quality (the paper's own F1 metric is circular, so an independent quality check matters). Rough cost: $5-10.
- Source: GitHub trending (topics: mcp, agents), week of 2026-07-20

---

## 2026-07-21 — proposed by research-scout

### ["C²KV": Compressed and Composable KV Cache Reuse for Efficient LLM Inference](https://arxiv.org/abs/2607.17715)
- Status: proposed — awaiting review
- Claim: A unified framework for non-prefix KV cache reuse that jointly learns compressed, composable KV representations (a joint extraction + inference-time concatenation objective), so document KVs stay reusable across different contexts/orderings even under aggressive compression; on Llama3.1-8B-scale QA/summarization tasks it shows graceful degradation and stays substantially more robust than prior KV-reuse methods as the compression ratio increases, including a variant trained with dynamically sampled compression ratios.
- Why it matters: Bridges the two KV-cache angles already queued separately — raw, uncompressed cache reuse across calls ("Can I Buy Your KV Cache?") and single-generation sliding-window compression (KARA) — by testing whether compression and cross-context composability can coexist, a distinct serving-infra mechanism from either queued candidate.
- Testability: Needs a GPU and an open-weight model (Llama3.1-8B-class; not reproducible through the Claude API) — out of scope for CPU-only Apple Silicon. A small open model on a Modal A10G could verify directionally whether compressed/composed KV segments degrade gracefully vs. naive prefix-caching or KARA-style compression on a small QA eval subset. Rough Modal cost: $15-25 for a few hours of A10G time — near the top of the per-experiment budget; would need tight scoping (small model, small eval set, 2-3 compression ratios) to fit.
- Source: arXiv cs.DC/cs.CL (2607.17715), submitted 2026-07 (recent)

### [Two Silent Traps in Agentic LLM Evaluation: Vanishing Tool Calls and Disagreeing Judges](https://huggingface.co/blog/GurkanOz/agentic-eval-two-traps)
- Status: proposed — awaiting review
- Claim: Companion write-up to a 4-bit-quantization survival study on a single DGX Spark (GB10): fine-tuning Qwen3-8B on well-formatted tool-calling data with `enable_thinking=False` silently breaks tool-calling entirely at inference time (training loss converges fine at 0.16, but the model never calls a tool again, instead confidently hallucinating answers) — caused by an asymmetry in how Qwen3's chat template renders the empty `<think>` block between train-time and inference-time. Separately, the same study shows LLM-as-judge scoring of agentic trajectories is sensitive to judge-rubric framing, causing judges to silently disagree about what's being measured.
- Why it matters: A measurement-methodology risk squarely inside this repo's own mission of testing whether claims hold up "with enough rigor to publish" — flags two specific silent-failure modes (a chat-template bug, and judge-rubric sensitivity) that could invalidate any future experiment here that fine-tunes a small open model for tool use or leans on an LLM judge for scoring.
- Testability: The chat-template half is essentially free and needs no GPU — just diff the Qwen3-family chat template's train-time vs. inference-time rendering under `enable_thinking=False` to confirm the mismatch exists, no training required to demonstrate it. Fully reproducing the "SFT silently breaks tool-calling" result needs an actual LoRA fine-tune of Qwen3-8B on a GPU — feasible on Modal (A10G), rough cost $10-20 for a short run. The "disagreeing judges" half is pure API, cheap to test with Haiku 4.5/Sonnet 4.6 as differently-rubric'd judges over a toy agentic trajectory set, roughly $5.
- Source: Hugging Face blog — GurkanOz, published 2026-07

---

## 2026-07-27 — proposed by research-scout

### [Rethinking the Evaluation of Harness Evolution for Agents](https://arxiv.org/abs/2607.12227)
- Status: proposed — awaiting review
- Claim: On Terminal-Bench 2.1 with GPT-5.4 and Claude Opus 4.6, automatic harness-evolution methods (which search/revise harness configs using task feedback) do not consistently beat simple test-time-scaling/discovery baselines under matched feedback and inference budgets, and evolved harnesses generalize poorly to held-out tasks — much of the reported "harness evolution" gain looks like search-budget leakage, not a real harness effect.
- Why it matters: A direct, high-value skeptical check on the whole cluster of self-evolving-harness candidates already queued here (Self-Harness, GenericAgent, Harness Updating Is Not Harness Benefit, Recursive Agent Harnesses) — if this holds up, it predicts several of those candidates will show the same "gain vanishes under a matched-budget baseline" pattern this repo's own scoreboard already documents for hand-designed harnesses.
- Testability: Very feasible, API only. Reuse whatever toy harness-evolution loop gets built for the already-queued Self-Harness candidate; add a matched-budget "simple test-time scaling" baseline (e.g. best-of-N or plain retry) and a held-out task split, using Haiku 4.5/Sonnet 4.6. No GPU. Rough cost: $10-15, well within the $25 budget.
- Source: arXiv cs.AI (2607.12227), submitted 2026-07-16

### [Harness-Bench: Measuring Harness Effects across Models in Realistic Agent Workflows](https://arxiv.org/abs/2605.27922)
- Status: proposed — awaiting review
- Claim: Introduces a diagnostic benchmark that holds tasks, budgets, and evaluation protocol fixed while varying only harness configuration (context/tool/state/permission/tracing/recovery management) across multiple model backends, to isolate how much of agent performance is attributable to the harness layer vs. the base model — where prior benchmarks conflate the two by comparing complete, differently-harnessed systems.
- Why it matters: This is an actual benchmark implementation of the exact methodological point the already-queued position paper "Stop Comparing LLM Agents Without Disclosing the Harness" argues for — a natural pairing, and this repo's own scoreboard (naive vs. structured harness × Haiku vs. Sonnet) is already a small instance of the same design, so this gives a cleaner protocol to fold that data into.
- Testability: Very feasible, API only. Apply a scaled-down version of their protocol directly to this repo's existing naive/structured harness code, fixed tasks and budgets, across Haiku 4.5 and Sonnet 4.6; largely a re-analysis with a small confirmatory run. No GPU. Rough cost: $5-10 for the new run.
- Source: arXiv cs.AI (2605.27922), submitted 2026-05-27

### [Where Does Agent Reliability Come From? A Cross-Benchmark Decomposition of Verification Loops, Specialist Models, and Scaffolding in a Production Enterprise Agent](https://arxiv.org/abs/2607.17044)
- Status: proposed — awaiting review
- Claim: A production enterprise agent (Leni) that adds verification-loop checkpoints (execute, observe, compare, correct) staffed by lightweight task-specialized models improves over its frontier base model by +11.0pp on SpreadsheetBench Verified (91.25% vs 80.25%, n=400, p<0.001), +7-10pp on BullshitBench v2 (98% vs 91%, n=100), and ~+15pp on GAIA validation (75.2% pass@1, n=165), attributing most of the gain to scaffolding/verification rather than the base model.
- Why it matters: A rare *positive* scaffolding result with real numbers and significance testing, sitting in direct tension with this repo's own scoreboard (three rows showing structured harnesses cost more for zero or negative gain) — worth checking whether the specific mechanism (execute→observe→compare→correct checkpoints) is what makes the difference vs. the already-tested "1-feature/session" structuring.
- Testability: Feasible small-scale, API only. Build a toy verification-loop harness (execute/observe/compare/correct with a lightweight verifier step) vs. a single-pass baseline on a small task set with objectively checkable answers (spreadsheet-style computation or similar), using Haiku 4.5 and/or Sonnet 4.6. No GPU. Rough cost: $10-15; won't match GAIA/SpreadsheetBench scale, only the directional "does the verification loop earn its keep" check.
- Source: arXiv cs.AI (2607.17044), submitted 2026-07-17

### [Keeping the Cache Warm Pays: Keepalive Economics for Agentic Workloads](https://arxiv.org/abs/2607.19214)
- Status: proposed — awaiting review
- Claim: Agentic workloads (request → tool call/approval wait of minutes → follow-up) routinely let the provider's prompt-prefix cache expire before the follow-up request, forcing a full-price prefill; a client-side keepalive that replays the prefix on a timer during the pause keeps it warm across Anthropic, OpenAI, Google, and DeepSeek, cutting post-pause request cost by up to 12.5x.
- Why it matters: A direct, cheap follow-on to this repo's own tested TokenPilot result, where ~⅘ of the measured savings turned out to be from enabling prompt caching in the first place — this tests whether a simple keepalive captures *additional* savings specifically during the idle/tool-wait gaps that TokenPilot's setup didn't isolate.
- Testability: Very feasible, API only, directly measurable via Anthropic's own billed cache-hit/miss pricing. Build a small toy agent task with an artificial multi-minute pause (simulating a tool call/approval wait) using Haiku 4.5 and/or Sonnet 4.6 with prompt caching enabled, compare billed cost with vs. without a periodic keepalive ping during the pause. No GPU. Rough cost: $5-10.
- Source: arXiv cs.DC (2607.19214), submitted 2026-07-21

### [CacheWise: Understanding Workloads and Optimizing KVCache Management for Efficiently Serving LLM Coding Agents](https://arxiv.org/abs/2606.16824)
- Status: proposed — awaiting review
- Claim: Real-world coding-agent traces show sessions repeatedly reuse large prompt prefixes, creating sustained KV-cache pressure that conventional vLLM eviction policies handle poorly; CacheWise (prefix-aware scheduling + reuse-aware eviction guided by tool-call-metadata predictions) reduces KV-cache evictions by up to 2-2.6x and improves total agent session completion time by up to ~3.5x.
- Why it matters: A serving-infra claim specifically about coding-agent workloads (not generic chat), complementing this repo's own harness experiments (one of which is a mini SQL-engine coding task) — tests whether reuse-aware eviction actually beats default vLLM policy on agent-shaped traffic patterns.
- Testability: Needs vLLM and a GPU — not feasible on CPU-only Apple Silicon. A small open model on a Modal A10G/T4 running vLLM, with a synthetic coding-agent-shaped trace (repeated prefix reuse + tool-call interleaving), comparing default vLLM eviction vs. a simplified prefix/reuse-aware policy. Rough Modal cost: $15-25 for a few hours of GPU time — near the top of the per-experiment budget; needs a small model and short trace set to fit.
- Source: arXiv cs.DC (2606.16824), submitted 2026-06-15

### [Give Them an Inch and They Will Take a Mile: Understanding and Measuring Caller Identity Confusion in MCP-Based AI Systems](https://arxiv.org/abs/2603.07473)
- Status: proposed — awaiting review
- Claim: MCP servers implicitly assume all tool invocations come from a single trusted caller, but in practice are frequently reused across multiple agents/scripts/applications on the same host; an authorization decision granted during one legitimate interaction can silently govern subsequent tool invocations from an entirely different caller ("caller identity confusion"), which a large-scale analysis of real MCP clients/servers shows is a widespread, previously underexplored vulnerability.
- Why it matters: A distinct, concrete MCP vulnerability class from the already-queued prompt-injection-focused security papers ("Breaking the Protocol," MCP-DPT) — this is about session/authorization boundary confusion between callers sharing one MCP server, not injected instructions, and is a natural fit alongside the other mock-MCP-server security candidates already queued.
- Testability: Cheap and GPU-free. Build one minimal mock MCP server shared by 2+ simulated callers/sessions, grant an authorization decision under one caller, and measure how often it silently carries over to a different caller's subsequent invocation, with and without a simple caller-identity-binding fix, using Haiku 4.5/Sonnet 4.6 as the driving agents. Rough cost: $5-10 in API calls.
- Source: arXiv cs.CR/cs.AI (2603.07473), submitted 2026-03-07

---

## 2026-07-28 — proposed by research-scout

### [The Interplay of Harness Design and Post-Training in LLM Agents](https://arxiv.org/abs/2606.25447)
- Status: proposed — awaiting review
- Claim: Extending ALFWorld to treat harness design (tool exposure, descriptions, per-step observation richness) as a controllable variable, performance improves monotonically with harness informativeness; under tool/task distribution shift, harness-aware post-training stays robust while post-training under a low-design-effort harness suffers drastic OOD collapse — i.e. harness design and post-training are not separable choices.
- Why it matters: A more fundamental claim than the already-queued harness-benefit papers — this says harness quality doesn't just affect zero-shot scores but determines whether post-training itself generalizes, relevant to any future experiment here that fine-tunes or RL-trains against a fixed harness rather than just prompting against one.
- Testability: Partially feasible without real training. Test the "informativeness → performance" and "OOD robustness" claims directionally using in-context few-shot conditioning as a stand-in for post-training, comparing 2-3 harness informativeness tiers under in-distribution vs. shifted tools on a toy ALFWorld-style task, with Haiku 4.5/Sonnet 4.6. No GPU. Rough cost: $10-15. The paper's actual RL post-training component is out of budget for this repo (would need real fine-tuning); this replicates only the harness-informativeness/OOD-robustness pattern.
- Source: arXiv cs.AI (2606.25447), submitted 2026-06-24

### [Speculate with Memory: Lossless Acceleration for LLM Agents](https://arxiv.org/abs/2607.12236)
- Status: proposed — awaiting review
- Claim: Equips agent-level speculative execution (a smaller model predicting/pre-launching the next action while the environment is idle) with three online memory systems — a contrastive transition table, episodic memory, and a confusion tracker; memory-augmented speculation improves action-prediction accuracy 19-39% relative and up to 2.5x on observation-prediction with repetitive action spaces, rising from ~28% to over 50% accuracy as experience accumulates, versus a flat stateless baseline.
- Why it matters: A different speculative-decoding angle from the queued token-level DSpark — this speculates at the agent-action level (which tool/action comes next), directly testable through the Claude API (small model predicts, large model verifies) rather than needing raw logits/KV access like every other speculative-decoding/KV-cache candidate already queued.
- Testability: Very feasible, API only, no GPU. Build a toy repetitive-task agent loop, use Haiku 4.5 as the memory-augmented speculator (predicting Sonnet 4.6's next tool call) with a simple transition-table + episodic-memory implementation, measure prediction accuracy with vs. without memory as trials accumulate. Rough cost: $5-15 — genuinely cheaper than the other serving-lane candidates already queued since it needs no GPU at all.
- Source: arXiv cs.CL/cs.AI (2607.12236), submitted 2026-07-14

### [Agentic Context Management: Solving Agent Memory and Cost by Treating Them as Lifecycle and Architecture Problems](https://arxiv.org/abs/2607.21503)
- Status: proposed — awaiting review
- Claim: Frames agent context management as five primitives (architecting, ingesting, scoping, anticipating, compacting & consolidation), arguing naive context accumulation grows token cost quadratically in conversation length, crude summarization buys linear cost at an accuracy cliff, and only validated compaction achieves linear cost with preserved fidelity; a reference implementation (Maximem Synap) reports 92% on LongMemEval and 93.2% on LoCoMo.
- Why it matters: The newest and most structurally complete entry in the context-management line already well-represented in this queue (Less Context Better Agents, ARC, GenericAgent, TokenPilot) — its distinct contribution is the quadratic-vs-linear cost argument and "validated compaction" as a named third option between raw accumulation and lossy summarization, worth checking against the already-queued candidates' pruning/summarization approaches directly rather than in isolation.
- Testability: Feasible, API only. Build a toy long-conversation task, measure actual token cost growth (quadratic vs. linear) across naive accumulation, plain summarization, and a simplified "validated compaction" (compact + a cheap consistency check before discarding) using Haiku 4.5/Sonnet 4.6 on a small LongMemEval-style QA subset. No GPU. Rough cost: $10-15; full LongMemEval/LoCoMo scale and the Maximem Synap implementation are out of scope — this is a directional cost-curve + accuracy check.
- Source: arXiv cs.AI/cs.CL (2607.21503), submitted 2026-07-23

### [MCPEvol-Bench: Benchmarking LLM Agent Performance Across Dynamic Evolutions of MCP Servers](https://arxiv.org/abs/2607.14642)
- Status: proposed — awaiting review
- Claim: New benchmark applying 11 mutation operators to simulate realistic tool-interface evolution across 123 real MCP servers, benchmarking 12 SOTA LLMs on multiple mutated versions of the same servers to measure how much task performance degrades when tool schemas/behavior drift after an agent has learned to use them.
- Why it matters: A distinct MCP-lane angle from every MCP paper already queued (prompt-injection security, production design patterns, defense-placement taxonomy, server-collaboration efficiency) — this is about robustness to tool *drift*, a realistic production failure mode for any long-lived MCP-based harness this repo might build.
- Testability: Feasible, API only. Build 2-3 mock MCP-style tools, apply a handful of the paper's mutation operator types (renamed params, changed return schema, added required field) mid-task, measure Haiku 4.5/Sonnet 4.6 task completion before vs. after mutation. No GPU. Rough cost: $5-10; won't replicate the 123-server/12-model scale, only the directional "does tool drift break agents mid-task" check.
- Source: arXiv cs.AI/cs.SE (2607.14642), submitted 2026-07-16

### [vLLM Semantic Router](https://github.com/vllm-project/semantic-router)
- Status: proposed — awaiting review
- Claim: An intelligent mixture-of-models router that classifies query complexity/intent and routes between small and large models plus a semantic cache layer; reports 10.2% accuracy improvement, 47.1% latency reduction, and 48.5% token-usage reduction on MMLU-Pro vs. always using the larger model, and separately claims a lightweight 8B model can recover most of a 235B model's performance on persistent user-specific queries via conversational-memory-grounded routing, cutting effective inference cost ~96%.
- Why it matters: A serving-infra technique squarely in the LLM-serving lane that's directly testable with the Claude API (route between Haiku and Sonnet) rather than needing raw model weights — distinct from every KV-cache/speculative-decoding candidate already queued, all of which need GPU/open-weight access; this one doesn't.
- Testability: Very feasible, API only, no GPU. Build a small mixed-difficulty eval set (easy factual + hard multi-step reasoning), implement a simple complexity classifier routing easy queries to Haiku 4.5 and hard ones to Sonnet 4.6, compare cost/latency/accuracy vs. an always-Sonnet baseline. Rough cost: $5-10 — one of the cheapest candidates in this batch, since routing itself saves money.
- Source: GitHub trending (python) / vLLM blog, project active as of blog post 2026-07-21 ("Beyond a Single Model: Building Mixture-of-Models Systems with vLLM Semantic Router")

---

## 2026-07-29 — proposed by research-scout

### [The new rules of context engineering for Claude 5 generation models](https://claude.com/blog/the-new-rules-of-context-engineering-for-claude-5-generation-models)
- Status: proposed — awaiting review
- Claim: Anthropic removed over 80% of Claude Code's system prompt for Claude 5-generation models (Opus 5, Fable 5) — replacing hard-coded rules/examples/always-on playbooks with judgment, interface-encoded constraints, and on-demand skills — with "no measurable loss" on internal coding evaluations.
- Why it matters: A direct, numbers-adjacent claim about harness/prompt overhead from the same lab whose models this repo already tests — squarely extends the scoreboard's own finding that structured/verbose harnesses often cost tokens for no quality gain, but here the claimed direction is reversed (less structure, same quality) rather than harness structure being neutral-to-harmful.
- Testability: Very feasible on Apple Silicon/API only. Build two system-prompt variants (a verbose rule-heavy one vs. a pruned/skill-based one) for a toy coding-agent task, run both against Haiku 4.5 and Sonnet 4.6 on a small held-out task set, and compare pass rate and token cost. No GPU. Rough cost: $5-10 in API calls; won't replicate Anthropic's internal eval suite, only the directional "does trimming the system prompt cost accuracy" check.
- Source: Anthropic Engineering blog (claude.com/blog), published 2026-07-24

### [A-TMA: Decoupling State-Aware Memory Failures in Long-Term Agent Memory](https://arxiv.org/abs/2607.01935)
- Claim: Identifies "ghost memory" — a state-coordination failure where old, current, and transition facts coexist and get mixed during retrieval, misleading the answer model; a state-aware overlay (A-TMA) that separates current/historical/transition evidence improves conflict accuracy by +0.240 absolute over Graphiti/Zep and raises temporal F1 on LoCoMo from 0.0295 to 0.1705.
- Status: proposed — awaiting review
- Why it matters: A different, sharply-quantified memory failure mode (temporal/state conflict, not verbosity or missed reminders) from the other memory candidates already queued or above — directly testable since it's an overlay on existing memory systems rather than a full redesign.
- Testability: Feasible small-scale, API only. Build a small conflict-heavy multi-session QA set (à la LoCoMo-Temporal-Plus but ~10-20 conversations), run a simple memory store with vs. without a state-aware overlay tagging current/historical/transition facts, using Haiku 4.5/Sonnet 4.6 as the answer model. No GPU. Rough cost: $5-10.
- Source: arXiv cs.CL/cs.AI (2607.01935), submitted 2026-07-01

### [SkillCorpus: Consolidating and Evaluating the Open Skill Ecosystem for Real-World LLM Agents](https://arxiv.org/abs/2607.15557)
- Status: proposed — awaiting review
- Claim: Filters ~821,000 crawled community agent skills (SKILL.md-style reusable procedural knowledge) through a multi-stage pipeline into a curated, taxonomy-organized corpus of 96,401 skills with quality scoring, paired with a fine-tuned retrieval/selection stack; integrating SkillCorpus yields consistent gains across three benchmarks, largest on SkillsBench (+7.5pp).
- Why it matters: A "does external community skill reuse actually help" claim distinct from the already-queued GenericAgent (self-generated SOPs from an agent's own trajectories) — this is about retrieval quality from a large curated third-party corpus, directly relevant if this repo ever builds on Claude Skills.
- Testability: Feasible small-scale, API only. Curate a small (~50-100) subset of publicly available skills, build a simple retrieval-and-selection step, and compare a toy agent task's pass rate with vs. without skill retrieval using Haiku 4.5/Sonnet 4.6. No GPU. Rough cost: $5-10; won't replicate the 821K-skill corpus scale, only the directional "does curated retrieval help" effect.
- Source: arXiv cs.AI/cs.CL (2607.15557), submitted 2026-07-17, revised 2026-07-20

### [AgentRedBench: Dynamic Redteaming and Integration-Aware Defense for LLM Agents over SaaS Integrations](https://arxiv.org/abs/2606.02240)
- Status: proposed — awaiting review
- Claim: A dynamic-redteaming benchmark of 215 subtle underspecified-authorization attack scenarios across 24 enterprise SaaS integrations (Gmail, Salesforce, Jira, etc.) finds no-guard attack success rates ranging 32% (Claude Sonnet 4.6) to 81% (Gemini 3 Flash) across an 8-model panel; a deployable guard (AGENTREDGUARD) cuts online attack success by ~75-77pp with near-zero benign false positives.
- Why it matters: A different attack surface than the already-queued MCP-specific security candidates (Breaking the Protocol, MCP-DPT, FARMA/SENTINEL) — this targets indirect prompt injection via third-party SaaS tool responses the user doesn't control, a distinct and concrete production threat class worth a directional check.
- Testability: Feasible small-scale, API only. Build a handful of mock SaaS-style tool integrations with injectable underspecified-authorization attack payloads (~20-30 scenarios, not 215), run Haiku 4.5/Sonnet 4.6 with vs. without a simplified guard filter, measure attack success rate reduction. No GPU. Rough cost: $10-15.
- Source: arXiv cs.CR/cs.AI (2606.02240), submitted 2026-06-02

---

## 2026-07-30 — proposed by research-scout

### [Don't Blame the Large Language Model: How Agent Harness Evolution Shapes Coding Agent Quality](https://arxiv.org/abs/2607.03691)
- Status: proposed — awaiting review
- Claim: First controlled longitudinal study that fixes the model and varies only the agent harness (35 sequential real-world harness releases), measuring effect on SWE-bench effectiveness/efficiency — finds no statistically significant quality improvement across releases for a given fixed LLM despite continuous development and growing harness complexity.
- Why it matters: A near-exact, observational validation target for this repo's own thesis — all three scoreboard rows already show hand-designed harness structure costing tokens without earning quality back. This is the same question from a different angle: does real-world harness *evolution over time* (not a single naive-vs-structured comparison) actually pay off, or is it flat/negative like this repo already found.
- Testability: Feasible on Apple Silicon/API only. Pick an accessible open-source agent harness with git history (or construct a toy harness with a handful of synthetic "versions") and run a fixed model (Haiku 4.5 or Sonnet 4.6) against a small fixed task set (10-20 tasks) across several harness versions, checking whether pass rate trends up. No GPU. Rough cost: $10-20; won't match the 35-release/SWE-bench scale, only the directional "does harness evolution correlate with quality" check.
- Source: arXiv cs.SE (2607.03691), submitted 2026-07-04 — slightly outside the usual 3-week window but included as a clear, direct hit on this repo's own thesis, likely missed by earlier scouting passes.

### [Agent Governance Toolkit](https://github.com/microsoft/agent-governance-toolkit)
- Status: proposed — awaiting review
- Claim: A policy-enforcement/sandboxing layer wrapping arbitrary agent tools that makes action-level policy violations "structurally impossible" (deterministic application-layer authorization, per-agent identity/audit trails, tamper-evident decision records) rather than merely prompt-discouraged; claims coverage of all 10 OWASP Agentic Top 10 risk categories, backed by 992 conformance tests and ~5.5k GitHub stars.
- Why it matters: A harness-level authorization angle distinct from the already-queued MCP-protocol-level security papers (Breaking the Protocol, MCP-DPT) — this wraps arbitrary tools regardless of transport, and it's a real installable library rather than only a paper, directly testable against this repo's own toy harnesses.
- Testability: Very feasible on Apple Silicon — pure Python, no GPU, install locally. Wrap a handful of toy tools with policy.yaml rules, have Haiku 4.5/Sonnet 4.6 attempt both benign and adversarial/destructive actions with and without the governance wrapper, measure block rate and false-positive rate on legitimate actions. Rough cost: $5-10 in API calls for the agent's own actions.
- Source: GitHub trending (python, agent-framework/security topics)

---

## 2026-07-31 — proposed by research-scout

### [From Prompts to Contracts: Harness Engineering for Auditable Enterprise LLM Agents](https://arxiv.org/abs/2607.08028)
- Status: proposed — awaiting review
- Claim: Moving deterministic behavior (source-grounding, entity routing, output contracts, reproducible traces) out of prompts into code/manifests/schemas around a replaceable LLM boundary preserves task guarantees under substitution across 3 hosted models and holds full utility, while an external prompt/guardrail-only baseline on the same validation scenarios drops utility to 88/120.
- Why it matters: A concrete, numbers-attached "code-owned guarantees beat prompting alone" claim, directly testable with this repo's own naive-vs-structured-harness methodology — but for an auditability/determinism goal rather than raw task accuracy, which none of the scoreboard rows have targeted yet.
- Testability: Feasible, API only. Build a small grounded-QA/entity-routing task, implement (a) a prompt-only guardrail baseline and (b) a code-owned contract/schema harness, run both across 2-3 model substitutions (Haiku 4.5, Sonnet 4.6) and measure the utility/pass-rate gap. No GPU. Rough cost: $10-15.
- Source: arXiv cs.AI/cs.SE (2607.08028), submitted early-mid July 2026

### [HANDBOOK.md: A Benchmark for Long-Context Agentic Instruction Following](https://arxiv.org/abs/2607.25398)
- Status: proposed — awaiting review
- Claim: New 65-task benchmark drops an agent into a self-contained company environment (file workspace plus mock email/chat/calendar/issue-tracker/commerce services exposed over MCP) governed by an expert-written 20-124 page SOP; even frontier models fail most trials, with the best-reported model following the long policy correctly only ~36.2% of the time.
- Why it matters: A concrete "does the harness make the agent actually obey a long standing policy document, not just complete the task" benchmark — a policy-adherence angle distinct from every context-management/MCP candidate already queued here.
- Testability: Very feasible, API only. Build a scaled-down version (~10-15 tasks, a synthetic 10-20 page SOP, 2-3 mock MCP services), run Haiku 4.5 and Sonnet 4.6 with and without an explicit policy-checking harness step, and measure policy-adherence rate vs. task completion. No GPU. Rough cost: $5-15.
- Source: arXiv cs.AI/cs.CL (2607.25398), submitted late July 2026

### [An Empirical Study of Model Context Protocol Applications](https://arxiv.org/abs/2607.25635)
- Status: proposed — awaiting review
- Claim: Large-scale study of 1,723 real MCPApps mined from GitHub finds the ecosystem has converged on some integration practices (85.2% configure servers via files, 81.1% use an official SDK) but not others (no naming convention has emerged for server configuration), via a derived taxonomy (MCPAppTax) applied with an LLM-assisted classification pipeline.
- Why it matters: An empirical/descriptive complement to the already-queued MCP design-pattern and security candidates — grounds any future mock-MCP-server test harness here in what real client code actually does, rather than an idealized protocol description.
- Testability: Cheap and mostly a data-validation check rather than a controlled experiment. Sample ~20-30 real MCPApps from GitHub, classify their config/SDK/human-oversight patterns against the paper's taxonomy using an LLM-assisted pass (Haiku 4.5/Sonnet 4.6), and compare against the paper's reported proportions directionally. No GPU. Rough cost: under $5.
- Source: arXiv cs.SE (2607.25635), submitted late July 2026

---

## 2026-08-03 — proposed by research-scout

### [Stateless MCP has recaptured my interest (and inspired mcp-explorer and datasette-mcp)](https://simonwillison.net/2026/Jul/31/stateless-mcp/)
- Status: proposed — awaiting review
- Claim: Covers the 2026-07-28 Model Context Protocol spec revision — the largest change since MCP's launch — which removes the stateful initialize handshake and Mcp-Session-Id requirement, replaces server-initiated requests with a retry pattern, deprecates Roots/Sampling/Logging, and adds a versioned extensions framework, turning MCP servers into plain stateless HTTP endpoints; Simon Willison built new tooling (mcp-explorer, datasette-mcp) against it immediately.
- Why it matters: A structural protocol change to the exact spec this repo's already-queued MCP papers (MCPSec, CA-MCP, MCP-DPT, "Bridging Protocol and Production") were written against — some of their proposed fixes (e.g. session-based identity propagation) may not transfer cleanly to a stateless core, worth a quick compatibility check before running those.
- Testability: Cheap and GPU-free. Stand up one minimal MCP server against the new stateless 2026-07-28 spec (official SDK) alongside the old stateful spec, and re-run a small version of the already-queued MCP attack/timeout scenarios to see if going stateless changes results. No GPU. Rough cost: $5-10 in API calls; most effort is protocol/plumbing rather than model calls.
- Source: Blog — Simon Willison's Weblog, published 2026-07-31

### [OpenSpace: The Skill Management Layer for AI Agents](https://github.com/HKUDS/OpenSpace)
- Status: proposed — awaiting review
- Claim: A skill-management layer (retrieve/evaluate/share/evolve loop, with FIX/DERIVED/CAPTURED skill-evolution modes and a local-first execution harness that captures quality evidence from real task outcomes) reports, with the same frozen backbone model on Terminal-Bench 2.1: 65.2% cold-run to 78.7% warm-run as its trusted skill library evolves (+13.5 points).
- Why it matters: A concrete, large-effect-size self-evolving-skill/harness claim, pairing naturally with the queued "Rethinking the Evaluation of Harness Evolution" critique above — does the cold→warm gain survive a matched-budget test-time-scaling baseline, or is it mostly extra search/retries in disguise, the same question this repo's scoreboard has repeatedly asked of structured harnesses?
- Testability: Feasible on Apple Silicon/API. Local-first architecture — skills run locally, only LLM calls hit the API. Build a small toy task suite, run OpenSpace's cold vs. warm skill-evolution loop with Haiku 4.5/Sonnet 4.6, and compare against a matched-budget best-of-N baseline. No GPU. Rough cost: $10-15.
- Source: GitHub trending (python, topics: agents/llm)

---

## 2026-08-10 — proposed by research-scout

### [LongHorizon-Harness: Advancing Long-Horizon Agents for Real-World Tasks](https://arxiv.org/abs/2608.01964)
- Status: proposed — awaiting review
- Claim: Reformulates long-horizon execution as explicit task-state management (state lives outside the growing conversation context, updated only from independently-verified environment facts) via a Manage-Execute-Audit loop; lifts Qwen3.7-Plus from 51.8%→80.7% on WeaveBench, 69.7%→77.2% on Terminal-Bench 2.1, and 2.8%→8.3% on OSWorld 2.0, and raises Claude Opus 4.7 from 20.0%→34.3% on an OSWorld 2.0 subset.
- Why it matters: The single largest claimed effect size yet for "structure the harness, don't just accumulate context" — directly tests this repo's own DB-harness/stress-config finding (structured harness cost more for zero gain) against a mechanism specifically designed to avoid the failure mode blamed for those nulls (context accumulation + self-assessment drift), on real non-one-shot tasks similar in spirit to the SQL-engine experiment already on the scoreboard.
- Testability: Feasible small-scale on Apple Silicon/API only. Build a toy multi-step task with an external, verifiable state store (not the model's running context) and a lightweight manager/executor/auditor split, using Haiku 4.5 as executor and Sonnet 4.6 as manager/auditor; compare against the existing naive and structured-1-feature/session harnesses already in `experiments/`. No GPU. Rough cost: $10-20; full 3-benchmark, frontier-model scale is out of budget, this would be a directional replication on a toy task.
- Source: arXiv cs.AI (2608.01964), submitted 2026-08-02

### [PRO-LONG: Programmatic Memory Enables Long-Horizon Reasoning](https://arxiv.org/abs/2607.20064)
- Status: proposed — awaiting review
- Claim: Counter-narrative to compression-based context management — instead of pruning/summarizing, the harness appends the *entire* interaction log to a durable store and gives the agent coding-agent tooling (grep/search-style) to query it on demand. On the full ARC-AGI-3 public game set this improves over a base coding agent by +18.0 points average across frontier models, and matches or exceeds specialized memory harnesses at up to 76.1% pass@1 while using 4.2-5.8x fewer tokens than passing full context.
- Why it matters: Directly contradicts the premise of every context-*pruning* candidate already queued (Less Context Better Agents, TokenPilot, ARC, GenericAgent) — worth checking head-to-head whether "keep everything, search with code" beats "prune/summarize" on a shared toy task, since this repo's own scoreboard has consistently found structured/pruned harnesses underperform naive ones.
- Testability: Very feasible on Apple Silicon/API only. Give a toy long-horizon agent a local append-only log file plus a grep-like search tool (no vector DB needed) and compare token usage/task success against the already-implemented naive and pruned-context configs, using Haiku 4.5/Sonnet 4.6. No GPU. Rough cost: $10-15.
- Source: arXiv cs.CL/cs.AI (2607.20064v2), submitted 2026-07-20

### [EvolveNet: Collaborative Harness Evolution for Agent Self-Improvement](https://arxiv.org/abs/2608.04968)
- Status: proposed — awaiting review
- Claim: Argues that pooling all execution experience into one sequential harness-optimizer (the assumption behind prior self-evolving-harness work) breaks down in real deployments where users/orgs/environments generate isolated, unpoolable experience streams; proposes broadcasting a shared harness to data-local deployments that each evolve it independently on their own workload, then reconciling the divergent versions.
- Why it matters: A federated/multi-tenant angle distinct from the already-queued Self-Harness, Harness Updating Is Not Harness Benefit, and Recursive Agent Harnesses — those all assume one optimizer with pooled traces; this specifically tests what happens when harness evolution has to work *without* pooling, which is closer to how this repo's own harness experiments are run in isolated batches.
- Testability: Feasible small-scale, API only. Run 2-3 isolated toy-task streams (e.g. different feature sets on the existing SQL-engine harness), let each evolve its own harness copy independently with Haiku 4.5 as evolver, then compare a naive pooled-optimizer baseline vs. the federated-then-reconciled variant on a held-out task. No GPU. Rough cost: $10-15.
- Source: arXiv cs.AI (2608.04968), submitted 2026-08-04

### [ACM: Agentic Context Management for Long Horizon Tasks](https://arxiv.org/abs/2607.23809)
- Status: proposed — awaiting review
- Claim: Gives the agent purpose-built context-editing tools (rather than a rigid token-threshold trigger) so it autonomously decides when to compress, offloads discarded content to an external memory store, and queries it back on demand; a post-training pipeline builds high-quality demonstrations of this behavior, improving performance on agentic search and coding tasks (Meta/CMU).
- Why it matters: The compress-and-offload counterpart to PRO-LONG's keep-everything approach above — both are fresh (late July 2026) answers to the same context-management question this repo has already tested three ways (TokenPilot tested, ARC/GenericAgent/Less-Context-Better-Agents queued); running ACM and PRO-LONG on the same toy task would give a genuinely new head-to-head on this repo's own scoreboard.
- Testability: Feasible without GPU, though the post-training-demonstration component doesn't fit an API-only budget — a directional check would give the agent explicit compress/offload/query tools (skipping the post-training pipeline) and measure whether autonomous compression timing beats a fixed-threshold baseline, using Haiku 4.5/Sonnet 4.6. Rough cost: $10-15; the post-training claim itself is out of budget (would need weight updates).
- Source: arXiv cs.CL/cs.AI (2607.23809), submitted 2026-07-26 (Meta/CMU)

### [Spend Bits Where Queries Look: KV Cache Vector Quantization with Attention-Preserving Transforms](https://arxiv.org/abs/2608.04074)
- Status: proposed — awaiting review
- Claim: Formulates KV cache quantization as a transform-coding problem where distortion is measured as error in the *attention products* (not raw K/V error); derives a closed-form, non-orthogonal optimal key transform and MSE-optimal vector quantizers in the transform domain. At 2 bits/element, the resulting method (NOVA-KV) recovers most of the long-context retrieval accuracy lost by scalar quantization baselines at comparable throughput.
- Why it matters: A different serving-lane mechanism from the already-queued KV-cache candidates (Can I Buy Your KV Cache = reuse across calls; KARA = sliding-window eviction) — this is compression via a smarter transform/quantizer, testable on the same small-open-model setup already scoped for those.
- Testability: Needs a GPU and an open-weight model — not feasible on CPU-only Apple Silicon. A small open model (1-4B class) on a Modal A10G could compare vanilla FP16 KV cache vs. scalar quantization vs. a simplified attention-aware transform quantizer at 2-bit on a small long-context retrieval eval. Rough Modal cost: $15-25 for a few hours of A10G time — near the top of the per-experiment budget, needs tight scoping (small model, small eval set).
- Source: arXiv cs.LG/cs.DC (2608.04074), submitted 2026-08-04

### [MCP goes stateless: the 2026-07-28 specification](https://blog.modelcontextprotocol.io/posts/2026-07-28/)
- Claim: The biggest MCP spec revision since launch removes protocol-level sessions entirely (no more initialize handshake, no `Mcp-Session-Id` header, no GET stream) — every request becomes a single self-contained HTTP POST. Servers that need cross-call state must mint explicit, opaque handles (e.g. a `basket_id`) passed back as ordinary tool arguments instead of relying on an implicit session.
- Status: proposed — awaiting review
- Why it matters: A live infrastructure change directly in this repo's MCP lane, and a natural extension of the already-queued "Bridging Protocol and Production" (ATBA/SERF for flaky multi-tool setups) and PlanBench-XL (flaky tool registry) candidates — worth checking whether the new server-minted-handle pattern actually degrades task completion less than session-based state under server restarts/load-balancer failover, since that's the exact scenario the spec change is meant to fix.
- Testability: Very feasible, API-free infra test. Build one minimal mock MCP server on the old session-based transport and one on the new stateless/handle-based transport, inject mid-task server restarts or round-robin routing across replicas, and compare task completion rates for a toy multi-step tool-use agent (Haiku 4.5/Sonnet 4.6) across the two transports. No GPU. Rough cost: $5-10 in API calls — most of the cost here is engineering the two mock transports, not model spend.
- Source: Model Context Protocol Blog (official spec release), published 2026-07-28; also covered by Simon Willison's Weblog, 2026-07-31 ("Stateless MCP has recaptured my interest")

---

## 2026-08-11 — proposed by research-scout

### [HarnessBridge: Learnable Bidirectional Controller for LLM Agent Harness](https://arxiv.org/abs/2606.12882)
- Status: proposed — awaiting review
- Claim: A lightweight, end-to-end trainable harness controller — an observation projection that distills raw trajectories into decision-relevant state, and an action projection that maps proposed actions to executable transitions or trajectory-grounded rejections — matches or surpasses strong manually-engineered harnesses on Terminal-Bench 2.0 and SWE-bench Verified while substantially cutting token usage and trajectory length, and generalizes from smaller training-time generators to larger commercial models.
- Why it matters: Tests whether a *learned* harness controller can outperform this repo's hand-designed structured harnesses (all 3 scoreboard rows show hand-designed structuring losing to naive) — a different failure-avoidance strategy than the already-queued self-editing (Self-Harness) or freeze-after-training (Adapting the Interface) approaches.
- Testability: Feasible without real GPU training — approximate the "learned" projections with a small prompted filter (or a trivial local logistic/embedding classifier trained on CPU) rather than full RL/SFT, and compare token usage/trajectory length vs. a naive baseline on a toy multi-step tool task using Haiku 4.5 as the base agent. Pure API + a CPU-only toy classifier, no GPU needed. Rough cost: $10-15; won't replicate real end-to-end training or Terminal-Bench/SWE-bench scale, only the directional "does a lightweight learned filter beat naive/manual harnessing" check.
- Source: arXiv cs.AI (2606.12882), UCLA, submitted 2026-06-2026 (June)

### [Self-GC: Self-Governing Context for Long-Horizon LLM Agents](https://arxiv.org/abs/2607.00692)
- Status: proposed — awaiting review
- Claim: Turns agent context (user turns, tool spans, skill state) into indexed objects, has a side-channel planner propose fold/mask/prune actions, and lets the harness enforce recoverable sidecars and cache-aware commits; on a 33-session hard set this prunes 43.95% of prefix tokens while leaving 84.85% of future continuations unaffected, three planner backbones reach 91.27%-94.58% "no-impact" rates on a 332-session production suite, and a production online A/B cuts daytime average input tokens 10-15% (peak ~20%).
- Why it matters: A different context-lifecycle mechanism than the already-tested TokenPilot (compaction + eviction) and the queued ARC (reflection reorg) / GenericAgent (atomic tools + SOPs) — worth checking whether object-indexed governance with recoverable sidecars beats this repo's TokenPilot result (net ~28% context-mgmt win once caching itself is backed out).
- Testability: Feasible on Apple Silicon/API only. Build a toy multi-session tool-use task, implement a simplified fold/mask/prune planner (Sonnet 4.6 as side-channel planner, Haiku 4.5 as agent), measure prefix tokens pruned vs. downstream task success ("no-impact rate"). No GPU. Rough cost: $10-15.
- Source: arXiv cs.CL/cs.AI (2607.00692), Xiaohongshu, submitted 2026-07-01

### [LLM Agents Are Latent Context Managers: Eliciting Self-Managed Context via State Proprioception (VISTA)](https://arxiv.org/abs/2606.30005)
- Status: proposed — awaiting review
- Claim: A training-free, model-agnostic "proprioceptive dashboard" (VISTA) that exposes per-context-block token cost, recency, and access history, with reversible full-fidelity archiving, lets frontier models self-manage working memory with no fine-tuning — the same untrained interface transfers across million-, 100K-, and 10K-token-scale trajectories on LOCA-Bench, BrowseComp-Plus, and GAIA.
- Why it matters: A third context-management strategy alongside Self-GC (above) and the already-tested TokenPilot — instead of an external planner pruning for the agent (Self-GC) or cache-aware eviction (TokenPilot), VISTA just gives the model visibility and lets it decide; cheap to check whether visibility alone (no automated pruning) matches or beats automated approaches.
- Testability: Very feasible, API only. Implement a simple dashboard (per-block token/recency counters surfaced in the system prompt) on a toy long-horizon tool task, compare Haiku 4.5/Sonnet 4.6 self-managed context vs. naive accumulation and vs. an automated pruning baseline. No GPU. Rough cost: $5-10.
- Source: arXiv cs.CL/cs.AI (2606.30005), Tencent, submitted 2026-06-30 (v4)

### [Benchmarking the Benchmarks: Evaluating Benchmarks for Conversational Agents](https://arxiv.org/abs/2608.06329)
- Status: proposed — awaiting review
- Claim: A reference-free LLM-judge framework scores conversational-agent benchmarks on consistency, complexity, and policy coverage; validated against independent human annotations and shown to reliably distinguish benchmark quality across LLM-generated benchmarks of varying capability and under controlled quality-degrading perturbations.
- Why it matters: A meta-evaluation angle adjacent to the already-queued "Stop Comparing LLM Agents Without Disclosing the Harness" — that paper argues harness variance is under-disclosed; this one argues benchmark quality itself is unmeasured. Relevant because every experiment in this repo builds a small toy benchmark, and this offers a cheap sanity check for whether those toy benchmarks are any good.
- Testability: Very cheap, API only. Apply the framework's consistency/complexity/coverage scoring (via an LLM judge, e.g. Sonnet 4.6) to one of this repo's own existing toy benchmarks (e.g. the DB-harness task) plus a deliberately degraded variant, and check if it detects the quality difference. No GPU. Rough cost: ~$5.
- Source: arXiv cs.CL/cs.AI (2608.06329), submitted 2026-08-06

---

## 2026-08-12 — proposed by research-scout

### [OrchBench: Evaluating Multi-Agent Orchestration Plans in Isolation via Deterministic Simulation](https://arxiv.org/abs/2607.25656)
- Status: proposed — awaiting review
- Claim: End-to-end multi-agent execution conflates orchestration-plan quality with worker capability, tool reliability, and noise, and is expensive to scale for evaluation; OrchBench instead builds DAGs of task dependencies (controlled size/parallelism) and simulates a planner's subtask assignment, cross-agent information transfer, and retention ratios given a per-agent context limit and budget — and reports that simulated results correlate with real multi-agent execution outcomes.
- Why it matters: A cheap, decoupled way to screen orchestration-plan quality before spending on real multi-agent runs — directly relevant to any future multi-agent (not just single-agent-harness) experiment in this repo, and a natural complement to the queued "Recursive Agent Harnesses" and "When Agents Do Not Stop" candidates.
- Testability: Feasible without GPU. Build a small set of toy DAG-structured tasks with controlled parallelism, have Haiku 4.5/Sonnet 4.6 act as the orchestration planner, run the lightweight simulator, and spot-check simulated vs. a handful of real multi-agent executions for correlation. Rough cost: $10-15; won't validate correlation at the paper's scale, only a small directional check.
- Source: arXiv cs.AI/cs.MA (2607.25656), submitted 2026-07-28

### [loopx](https://github.com/huangruiteng/loopx)
- Status: proposed — awaiting review
- Claim: A local-first "state kernel" for long-running agent work (goals, executable todos, human-in-the-loop gates, evidence logs, quota-aware wake scheduling) that lets agents (Claude Code, Codex, Cursor) hand off work across sessions without losing state or over-spending after progress stalls; README cites anecdotal cases (200+ hours elapsed, 4-day unattended runs, multi-PR merges) rather than a controlled benchmark.
- Why it matters: A GitHub-trending tool making almost exactly the claim this repo's harness rows have been testing (does external state-structuring for long-running agent work pay for itself) — but with no controlled comparison yet, making it a good target for this repo's existing naive-vs-structured methodology rather than a paper to replicate.
- Testability: Feasible, API only, no GPU. Because there are no benchmark numbers to replicate, this would be a fresh controlled comparison (naive long-running agent vs. loopx's goal/todo/gate/evidence kernel) on a toy multi-session task, reusing this repo's existing harness-comparison scaffolding. Rough cost: $10-15. Flag: claims are currently anecdotal/qualitative, so frame any result as this repo's own finding, not a replication.
- Source: GitHub trending (python, agent-framework)

---

## 2026-08-14 — proposed by research-scout

### [Evo-Bench: Can Language Models Improve Agent Harness?](https://arxiv.org/abs/2608.09096)
- Status: proposed — awaiting review
- Claim: First benchmark designed to isolate an agent's intrinsic harness-evolving capability from base model strength (Search/Office/General domains, sensitivity-aware stratified splitting so gains can't be task-specific overfitting); across 9 frontier/open-weight models, top models gain up to +16.6 absolute points from autonomously evolving their own harness, closely approaching hand-engineered baselines — but autonomous evolution beats hand-engineering on Search/General while struggling on Office tasks needing highly specific workflows.
- Why it matters: The closest thing yet to a direct, controlled meta-test of this repo's whole thesis (three scoreboard rows already show hand-designed structured harnesses losing to naive) — its isolate-harness-from-model-strength eval design is itself reusable for future scoreboard rows, and it directly complements the already-queued Self-Harness / Harness-Updating candidates with an actual benchmark rather than a single technique.
- Testability: Feasible small-scale, API only. Skip the full 3-domain suite — build one toy domain (e.g. a small General-agent task set) using the same isolate-harness-effect logic (auxiliary-task evolution + stratified split), run Haiku 4.5 and Sonnet 4.6 each as their own harness-evolver, and compare gains. No GPU. Rough cost: $10-20.
- Source: arXiv cs.AI (2608.09096), submitted 2026-08 (~1 week old)

### [AgentMemBench: A Systematic Benchmark for Evaluating Long-Term Memory Management Strategies in Conversational AI Agents](https://arxiv.org/abs/2608.00009)
- Status: proposed — awaiting review
- Claim: Evaluates 5 memory strategies (in-context windowing, external key-value store, graph-based episodic memory, compression-based summarization, web-augmented memory) under identical conditions across 491 annotated multi-session QA turns (LoCoMo, MultiDoc2Dial, MSC); dense-embedding external KV retrieval (EKV) dominates every quality axis (macro Recall@5 0.354, best-in-class), while on the hardest long-range dataset all 5 strategies collapse to similarly poor recall (~0.573), suggesting the "fancy" graph/summarization approaches don't actually beat boring retrieval at small scale.
- Why it matters: A concrete, falsifiable ranking of memory strategies squarely in this repo's context/memory lane (TokenPilot tested, GenericAgent and TencentDB-Agent-Memory already queued) — worth checking whether "dense retrieval beats graph memory" replicates directionally, since it's a skeptical finding (simple beats complex) matching this repo's track record.
- Testability: Very feasible on Apple Silicon/API only. Implement 3-4 of the 5 strategies (graph-based episodic memory is the most complex, can be dropped) on a small multi-session QA task; use Haiku 4.5/Sonnet 4.6 for generation/judging and a local or API embedding model for EKV. No GPU needed. Rough cost: $5-15.
- Source: arXiv cs.CL/cs.AI (2608.00009), submitted 2026-08

### [Diagnosing Tool-Selection Reasoning in LLM Agents with Canary Tools](https://arxiv.org/abs/2608.04719)
- Status: proposed — awaiting review
- Claim: "Canary tools" — diagnostic probe tools planted in an agent's MCP tool set across a 6-type taxonomy (semantic decoys, parameter traps, capability mirages, prerequisite blindness, temporal decoys, granularity traps) — reveal, across 8,640 runs on 8 models, that capability tier does not predict tool-selection safety (a mid-tier hosted model is most susceptible; the cheaper model in a provider's lineup can be safer than the pricier one), and canary susceptibility predicts real downstream task failure.
- Why it matters: A mechanism-level MCP tool-selection diagnostic (why the wrong tool gets picked, not just that it was) — distinct from the already-queued PlanBench-XL (tool-registry reliability under blocking) and the MCP security papers, and directly reusable as a diagnostic against any harness this repo builds.
- Testability: Very feasible, API only. Build a small MCP-style tool set with 2-3 canary types planted, run Haiku 4.5 and Sonnet 4.6 across a reduced task set (~20-30 vs. their 120), check whether canary susceptibility predicts task failure directionally and whether it's capability-tier-independent. No GPU. Rough cost: $5-10.
- Source: arXiv cs.AI/cs.CL (2608.04719), submitted 2026-08-05

### [SHE: Trajectory-driven Safety Harness Evolution for LLM Agents](https://arxiv.org/abs/2608.09885)
- Status: proposed — awaiting review
- Claim: Decomposes an agent harness into 4 safety-relevant artifacts (System Prompt, Rule Bank, Safety Memory, Tool Policy) with explicit safety responsibilities, then runs an attribution-guided evolution loop converting trajectory failures into localized, artifact-specific boundary refinements — achieving a 3.1x attack-success-rate reduction vs. a static "SafeHarness" baseline on Agent-SafetyBench, while also improving benign-task utility (not just becoming more restrictive).
- Why it matters: A safety-specific variant of harness self-evolution, distinct from the capability-focused Self-Harness/Harness-Updating/Evo-Bench candidates — tests the stronger, more falsifiable claim that localized harness edits can improve safety AND utility together, worth checking against this repo's pattern of structured harnesses costing more for no measured gain.
- Testability: Feasible small-scale, API only. Build a toy adversarial-prompt suite (jailbreak-style + benign look-alikes), implement a simplified 4-artifact harness decomposition, run one evolution iteration with Sonnet 4.6 as evolver and Haiku 4.5 as executor, measure attack-success-rate and benign-completion rate before/after. No GPU. Rough cost: $10-15.
- Source: arXiv cs.AI/cs.CR (2608.09885), submitted 2026-08-10

### [Does Accuracy Equal Evidence? Reasoning Faithfulness under KV Cache Compression](https://arxiv.org/abs/2608.01631)
- Status: proposed — awaiting review
- Claim: Evaluating 10 token-eviction KV-cache-compression methods plus 1 quantization method across reasoning benchmarks, final-answer accuracy can look preserved while chain-of-thought faithfulness (whether the retained cache still actually supports the stated reasoning) substantially degrades — compressed models can land the right answer via unsupported/broken reasoning chains.
- Why it matters: A skeptical "does the headline number hide a real cost" critique of KV-cache compression — the same shape of finding this repo already produced for context management (TokenPilot: real but smaller win than claimed) and harnesses (cost without quality gain), applied to the serving lane. Complements queued KARA / Can-I-Buy-Your-KV-Cache with a critique angle instead of another technique.
- Testability: Needs a GPU + open-weight reasoning model (not reproducible via the Claude API) — out of scope for CPU-only Apple Silicon. A small open reasoning model (~1.5-7B) on a Modal A10G could test 2-3 eviction methods' accuracy-vs-faithfulness gap on a small reasoning-chain eval subset. Rough Modal cost: $15-25 for a few hours of A10G time — near the top of the per-experiment budget; needs tight scoping (2-3 methods, small eval set) to fit.
- Source: arXiv cs.CL/cs.LG (2608.01631), submitted 2026-08-01

---

## 2026-08-18 — proposed by research-scout

### [The Bitter Lesson of Tool Calling](https://arxiv.org/abs/2608.06370)
- Status: proposed — awaiting review
- Claim: A generation-spanning comparison of programmatic tool calling (tools exposed as typed Python stubs invoked through code, execution+results handled in one agent turn) vs. native JSON tool calling across 14 LLMs on BFCL v4 — programmatic calling matches or beats JSON in 11/14 models, with the GPT-5.6 family gaining +10.6% over the JSON baseline; wins 13/14 under parallel fan-out; and under "context rot" it holds steady while the JSON baseline drops 2.3% on average. The advantage grows with a model's code ability.
- Why it matters: A genuinely new angle not covered by anything already queued — every other tool-use candidate in this queue tests description quality, drift, blocking, or robustness of JSON-style calls; this tests the *interface paradigm itself* (code vs. JSON), directly actionable for how this repo's own `intervention.py` harnesses expose tools to agents.
- Testability: Very feasible, API only. Claude models can be prompted into both styles (native JSON tool_use vs. writing code against typed stubs). Build a small (~20-30 call) BFCL-v4-style toy eval including a parallel-fan-out condition and a long-context "rot" condition, compare JSON vs. code-based invocation with Haiku 4.5/Sonnet 4.6. No GPU. Rough cost: $5-10.
- Source: arXiv cs.CL (2608.06370), submitted 2026-08-06

### [Control Under Compression: Reliability Frontiers for Tool-Using Agents](https://arxiv.org/abs/2608.01056)
- Status: proposed — awaiting review
- Claim: Introduces CompressAgent, an environment-verified benchmark (9 agent control contexts, 3 task families, 3 Qwen models, 6 retained-context budgets, 15,525 runs) for compressing an agent's *control* context — the persistent system-side instructions specifying tools, arguments, policies, and recovery, not the conversation. Finds a nonlinear, method-dependent reliability frontier: at 75% retained context, generic/section-based compression stays near the 93.8% full-context baseline (92.7%/92.4%), but between 50% and 35% methods diverge sharply, collapsing to 47.0%/39.0%/19.9% success at 35% retention depending on method.
- Why it matters: Distinct from every already-queued context-pruning candidate (all of which target conversational history or tool-output verbosity) — this compresses the harness's own control instructions, directly analogous to this repo's hand-written structured-harness prompts, and gives a concrete "how far can the harness prompt itself be trimmed before reliability collapses" number worth checking against this repo's own naive/structured configs.
- Testability: Very feasible, API only. Take this repo's own structured-harness control instructions, build 2-3 compression variants at different retention levels, run against a small multi-step tool task with Haiku 4.5/Sonnet 4.6, and measure success rate vs. retention %. No GPU. Rough cost: $10-15.
- Source: arXiv cs.CL/cs.AI (2608.01056), submitted 2026-08-02

### [Exposed by Design: A Dynamic Security Assessment of Internet-Facing MCP Servers at Scale](https://arxiv.org/abs/2608.00150)
- Status: proposed — awaiting review
- Claim: First dynamic behavioral security scan of real internet-facing MCP servers (passive discovery across 11 sources + Corvus, a purpose-built active-testing framework with 34 test modules covering 10 MCP-specific vulnerability classes). Across 4 measurement runs in July 2026: confirms 640 production MCP servers, dynamically audits 414, finds 68 reportable vulnerabilities (SQL injection, SSRF against cloud metadata services, prompt-template injection, path traversal via cursor manipulation); 91.8% of audited servers lack OAuth authentication; 687 tool instances expose shell execution with no access control; 41.6% of confirmed servers disappear within 3 days between runs.
- Why it matters: Every MCP-security candidate already queued (Breaking the Protocol, MCP-DPT, caller-identity-confusion, MCPEvol-Bench) tests against a mock/theoretical MCP server or attack taxonomy — this is real production-MCP-server telemetry, putting hard numbers on how exposed the actual ecosystem is right now, a more empirical/skeptical check than any queued security paper.
- Testability: Feasible without touching third-party infra. Reproduce directionally by running a handful of your own locally-hosted mock MCP servers through a reduced subset of simple checks inspired by Corvus's test modules (missing auth, unrestricted shell-exposed tools) — no scanning of real public servers without authorization. No GPU; a small amount of API budget if using Haiku 4.5/Sonnet 4.6 to help triage findings. Rough cost: under $5.
- Source: arXiv cs.CR/cs.AI (2608.00150), submitted 2026-08-01

### [When Memory Becomes Authority: Benchmarking Authority Collapse at the Memory Consolidation Boundary](https://arxiv.org/abs/2608.01679)
- Status: proposed — awaiting review
- Claim: Introduces AuthMem-Bench, a paired benchmark holding the focal claim and downstream task fixed while varying only the memory's *source authority* (e.g. user-stated fact vs. one-off agent observation vs. standing policy instruction). Finds "authority collapse" — consolidation preserves the claim but erases the source constraints on how it may be used, so the stored memory implies more authority than its origin permits — in 48 of 49 evaluated consolidator × LLM-backbone configurations.
- Why it matters: A distinct, sharply-quantified memory failure mode from every memory candidate already queued (MemSyco-Bench = sycophancy toward retrieved memory; A-TMA = temporal/state conflict) — this is about the authorization boundary silently eroding during consolidation, e.g. a casual one-off observation later being treated as a standing instruction. Directly relevant to any future harness experiment here that adds persistent memory with any notion of trust tiers.
- Testability: Very feasible, API only. Build a small (10-20) paired toy set where the same claim originates from different authority sources, run a simple consolidation step then a downstream task with Haiku 4.5/Sonnet 4.6, and measure how often a low-authority memory gets treated as high-authority downstream. No GPU. Rough cost: $5-10.
- Source: arXiv cs.AI/cs.CL (2608.01679), submitted 2026-08-03

### [AI Agents Do Not Fail Alone: The Context Fails First](https://arxiv.org/abs/2607.14275)
- Status: proposed — awaiting review
- Claim: Validates context-engineering quality (role clarity, guardrail coverage, instruction consistency, tool-schema quality, grounding sufficiency, injection hardening) as an independent leading indicator of agent reliability, measured via an open-source multi-juror consensus-scoring harness (ProofAgent-Harness) rather than task outcome alone.
- Why it matters: A measurement-methodology angle distinct from every context-management technique already queued — instead of proposing another pruning/compaction mechanism, this proposes a diagnostic *score* for context quality itself, which could be applied to re-audit this repo's own existing naive vs. structured harness configs before running a new head-to-head comparison.
- Testability: Very cheap, API only. Implement a scaled-down version of the scoring rubric as an LLM-judge pass (Sonnet 4.6) applied to this repo's own existing harness prompts (naive vs. structured, already on the scoreboard) plus a deliberately degraded variant, and check whether the score tracks the scoreboard's own measured outcomes. No GPU. Rough cost: under $5.
- Source: arXiv cs.AI/cs.CL (2607.14275), submitted 2026-07-15 — slightly outside the usual 3-4 week window but not previously surfaced or queued, and squarely on this repo's own thesis.
