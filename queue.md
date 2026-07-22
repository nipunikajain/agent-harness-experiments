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

### [Harness Updating Is Not Harness Benefit: Disentangling Evolution Capabilities in Self-Evolving LLM Agents](https://arxiv.org/abs/2605.30621)
- Status: proposed — awaiting review
- Claim: Disentangles two capabilities in self-evolving harness agents — "harness-updating" (producing useful persistent harness updates from execution evidence) is flat across model capability tiers, while "harness-benefit" (actually benefiting from those updates during task-solving) is non-monotonic: weak-tier models gain little because they fail to activate relevant harness artifacts or follow them faithfully once activated, even when the updates themselves are just as good as a stronger model's.
- Why it matters: A skeptical, diagnostic paper that directly parallels this repo's own findings (structured harnesses repeatedly showing cost without quality gain, especially on Haiku) — offers a concrete hypothesis for *why* weaker models might fail to benefit from harness structure even when the harness content is sound, and is a natural stress test alongside the already-queued Self-Harness.
- Testability: Feasible small-scale, API only. Have both Haiku 4.5 and Sonnet 4.6 generate harness updates from the same shared set of induced failure traces on a toy task, then cross-apply updates (e.g. give Haiku 4.5 the Sonnet-authored updates) to see whether the weaker model still under-benefits even from stronger-model-authored harness content. No GPU. Rough cost: $10-15.
- Source: arXiv cs.AI/cs.CL (2605.30621), submitted 2026-05-30

### [Adapting the Interface, Not the Model: Runtime Harness Adaptation for Deterministic LLM Agents](https://arxiv.org/abs/2605.22166)
- Status: proposed — awaiting review
- Claim: Life-Harness converts recurring interaction failures observed during a training phase into reusable interventions across four categories (environment contracts, procedural skills, action realization, trajectory regulation), then freezes the harness for evaluation on unseen tasks — improving 116 of 126 model×environment settings across 18 model backbones on τ-bench, τ²-bench, and AgentBench, averaging +88.5% relative improvement, without changing model weights.
- Why it matters: A much larger claimed effect size than this repo's own tested "1-feature/session" structuring (which found zero benefit for real cost) — the key structural difference is "freeze after training, no further per-session overhead at eval time," which is exactly the failure mode the scoreboard rows blame for the tested harness's cost. Worth checking if freezing is the missing ingredient.
- Testability: Feasible small-scale, API only. Build a toy deterministic tool-use task (τ-bench-style), run a short "training" phase where Sonnet 4.6 mines a handful of induced failures into the four intervention categories, freeze the resulting harness, then evaluate both Haiku 4.5 and Sonnet 4.6 against a naive baseline on held-out tasks. No GPU. Rough cost: $10-20; won't match the 18-backbone/3-benchmark scale, only the directional "does freezing help" effect.
- Source: arXiv cs.AI (2605.22166), submitted 2026-05-22

### [Stop Comparing LLM Agents Without Disclosing the Harness](https://arxiv.org/abs/2605.23950)
- Status: proposed — awaiting review
- Claim: Position paper proposing the "Binding Constraint Thesis" — for long-horizon tasks evaluated across models of comparable frontier capability, harness configuration (context construction, tool interaction, orchestration, verification) explains more performance variance than model choice, sometimes reversing model rankings; proposes a harness-aware evaluation and disclosure standard with a variance-decomposition protocol.
- Why it matters: This is close to the theoretical frame this repo's entire scoreboard has been informally testing (three rows already show structured-harness cost without quality gain) — a direct opportunity to run the paper's own proposed variance-decomposition check at small scale using harness code this repo already has.
- Testability: Very feasible, API only. Fix a small task set, cross 2 harness configs (naive vs. one of the already-tested structured harnesses) with 2 models (Haiku 4.5, Sonnet 4.6), and compute a basic variance decomposition (harness-attributable vs model-attributable). No GPU, reuses existing repo code. Rough cost: $5-10.
- Source: arXiv cs.AI (2605.23950), submitted 2026-05-07

### [Better Models: Worse Tools](https://simonwillison.net/2026/Jul/4/better-models-worse-tools/)
- Status: proposed — awaiting review
- Claim: Blog post (Armin Ronacher, syndicated via Simon Willison) reporting that newer Claude models (Opus 4.8, Sonnet 5) invent extra, non-schema fields when calling a third-party harness's custom edit tool (the Pi editor), a regression not present in older models — hypothesized to result from RL post-training tuned specifically to Claude Code's own edit-tool schema, which fails to generalize to other harnesses' custom tool schemas.
- Why it matters: A concrete, falsifiable claim squarely in the agent-harness lane — if newer/"better" models are quietly worse at *custom* (non-Claude-Code) tool schemas, that's a direct risk for any harness in this repo built on bespoke tools rather than Claude Code's own conventions.
- Testability: Very cheap, API only. Define two edit-tool schemas — one mirroring Claude Code's own edit-tool field conventions and one deliberately different (custom field names/structure) — run a small battery of edit tasks against current models (Haiku 4.5, Sonnet 4.6) and measure schema-violation rate on the non-standard schema. No GPU. Rough cost: $5-10.
- Source: Blog — Armin Ronacher (lucumr.pocoo.org), syndicated via Simon Willison's Weblog, published 2026-07-04

### [DSpark: Confidence-Scheduled Speculative Decoding with Semi-Autoregressive Generation](https://arxiv.org/abs/2607.05147)
- Status: proposed — awaiting review
- Claim: Combines a semi-autoregressive drafter (parallel backbone plus a lightweight sequential module to model intra-block token dependencies and mitigate "suffix decay") with confidence-scheduled verification (dynamically sizing verification length per request from estimated prefix-survival probability); deployed in DeepSeek-V4's serving system, it lifts per-user generation speed 60-85% at matched throughput and shifts the latency/throughput Pareto frontier.
- Why it matters: A concrete, falsifiable serving-infra claim in the LLM-serving lane — tests whether confidence-scheduled, variable-length speculative verification actually beats fixed-length speculative decoding, distinct from the queued KV-cache-reuse/compression candidates.
- Testability: Needs a GPU with an open draft/target model pair — not feasible on CPU-only Apple Silicon. A small open pair (e.g. a ~0.5-1B draft model with a 3-7B target) on a Modal A10G could directly compare fixed-length speculative decoding vs. a simplified confidence-scheduled variant on a small generation benchmark. Rough Modal cost: $15-25 for a few hours of A10G time — near the top of the per-experiment budget; would need tight scoping (small models, small eval set) to fit.
- Source: arXiv cs.LG/cs.DC (2607.05147), submitted 2026-07-06

### [Enhancing Model Context Protocol (MCP) with Context-Aware Server Collaboration](https://arxiv.org/abs/2601.11595)
- Status: proposed — awaiting review
- Claim: Proposes CA-MCP, restructuring stock (stateless) MCP so the central LLM handles only high-level planning and final summarization, while a Shared Context Store accessible to all MCP servers holds global context — aiming to cut redundant computation and improve coherence in multi-server agent workflows.
- Why it matters: A distinct MCP-infrastructure angle from the already-queued MCPSec (protocol security) — this is about efficiency/coherence of multi-server MCP workflows, directly testable with a small toy multi-server setup and squarely in this repo's MCP lane.
- Testability: Feasible, API only. Build 2-3 mock MCP servers with overlapping sub-tasks, compare token usage/redundant re-fetching and end-task coherence with vs. without a simple shared context store, using Haiku 4.5 and/or Sonnet 4.6. No GPU. Rough cost: $5-10.
- Source: arXiv cs.AI/cs.DC (2601.11595), submitted 2026-01-06, revised 2026-01-22

---

## 2026-07-22 — proposed by research-scout

### [Learning to Control LLM Agent Harnesses with Offline Reinforcement Learning](https://arxiv.org/abs/2607.05458)
- Status: proposed — awaiting review
- Claim: Formalizes the harness itself as a "Harness MDP" and trains a lightweight controller via offline advantage-weighted regression (terminal task-rubric rewards only, LLM executor frozen) to select structural execution actions; across six controlled domains plus two public-benchmark adapters (adapted τ-bench retail, adapted AgentBench DB-Bench, coding), the learned controller consistently improves verification behavior and selectively improves final task quality, measured separately via a post-hoc "Harness Maturity Score" vs. raw task correctness.
- Why it matters: The most direct match yet to this repo's core question — whether structured harness behavior is worth its cost. Rather than a hand-designed structured harness (already tested here, found costly with no quality gain) or a self-editing harness (queued Self-Harness), this treats harness control as a *learned policy* over structural actions — a distinct mechanism worth checking against the repo's existing null/negative results.
- Testability: Feasible small-scale, API-only. Build a toy Harness MDP with a handful of discrete structural actions (retry, verify-before-answer, request-more-context, escalate) on a toy tool-use task; collect offline rollouts with Haiku 4.5 as the frozen executor, fit a simple AWR-style controller (a small logistic/tabular policy is enough to test the mechanism, not a full deep-RL stack), and compare against this repo's already-tested naive/structured baselines, judged by Sonnet 4.6. No GPU. Rough cost: $10-20 for enough rollouts to fit and evaluate a controller.
- Source: arXiv cs.AI/cs.LG (2607.05458), submitted 2026-07-05

### [Model Context Protocol (MCP) Tool Descriptions Are Smelly! Towards Improving AI Agent Efficiency with Augmented MCP Tool Descriptions](https://arxiv.org/abs/2602.14878)
- Status: proposed — awaiting review
- Claim: Across 856 tools from 103 real-world MCP servers, 97% of tool descriptions contain at least one quality defect (56% don't clearly state what the tool does, 89% fail to say when it should/shouldn't be used); a follow-up finding cited alongside it reports well-written descriptions get selected 260% more often than poorly-written ones in competitive multi-server settings offering overlapping functionality.
- Why it matters: A concrete, MCP-specific *input-quality* claim distinct from the already-queued MCP security/production-pattern/collaboration candidates — this is about whether ordinary tool-description quality (not protocol architecture) drives agent tool-selection errors, directly testable with the same toy multi-MCP-server harnesses already proposed for other queued MCP candidates.
- Testability: Very cheap, API-only. Build 5-10 mock MCP tools with deliberately "smelly" descriptions (following the paper's defect taxonomy: missing purpose, missing usage guidance) vs. rewritten "clean" versions, run Haiku 4.5/Sonnet 4.6 on a tool-selection task where the correct tool is ambiguous without a good description, and measure selection accuracy and wasted steps. No GPU. Rough cost: $5-10.
- Source: arXiv cs.SE/cs.AI (2602.14878), submitted 2026-02-16

### [From Prompts to Contracts: Harness Engineering for Auditable Enterprise LLM Agents](https://arxiv.org/abs/2607.08028)
- Status: proposed — awaiting review
- Claim: Reconstructing a prototype LLM-agent pattern into a harness-engineered architecture — deterministic behavior moved into code, manifests, schemas, and validation artifacts around a replaceable composition boundary — preserves source-grounding, entity-routing, trace, output-hygiene, and recommendation-language contracts across fixed validation scenarios, and a fault-injection control confirms the validators correctly flag deliberately broken contracts (evaluated on a public-data slice of 5 Korean corporate groups, 25 listed companies).
- Why it matters: A production/enterprise "harness as contract enforcement" angle, adjacent to the already-queued CAAF (invariant-registry determinism) and Life-Harness (frozen post-training harness) candidates — worth checking whether contract validators actually catch injected failures reliably, or just add overhead the way the repo's tested structured harness did.
- Testability: Feasible, API-only. Build a small toy RAG/agent pipeline with 3-4 output "contracts" (e.g. source-grounding, entity-routing, output format) enforced by simple validators, run fixed scenarios plus a fault-injection set (deliberately broken contracts) against Haiku 4.5/Sonnet 4.6, and measure validator catch-rate and overhead vs. a no-validator baseline. No GPU. Rough cost: $5-10.
- Source: arXiv cs.CL/cs.AI (2607.08028), submitted 2026-07-09

### [Long-Horizon-Terminal-Bench: Testing the Limits of Agents on Long-Horizon Terminal Tasks with Dense Reward-Based Grading](https://arxiv.org/abs/2607.08964)
- Status: proposed — awaiting review
- Claim: A new 46-task, 9-category long-horizon terminal benchmark that decomposes each task into fine-grained graded subtasks for dense intermediate rewards and partial credit, arguing existing terminal benchmarks (e.g. Terminal-Bench-style final-outcome-only grading) give an incomplete picture of agent progress on long, multi-hundred-step workflows.
- Why it matters: A grading-methodology complement to the already-queued Self-Harness paper (which used Terminal-Bench-2.0's sparse pass-rate grading) — if this repo tests any harness-improvement claim on a terminal-style task, dense subtask grading could reveal whether "no measurable quality gain" verdicts (as already found for the repo's tested harness) are partly an artifact of sparse, final-outcome-only grading.
- Testability: Feasible at small scale. Pick a handful of the released tasks (or build 2-3 similar toy long-horizon terminal tasks) with dense subtask checkpoints, run naive vs. one of this repo's already-tested structured harnesses under both sparse (final-only) and dense grading, using Haiku 4.5/Sonnet 4.6. No GPU. Rough cost: $10-15; the full 46-task benchmark is out of budget — this would be a directional grading-methodology check reusing the repo's existing harness code.
- Source: arXiv cs.AI/cs.SE (2607.08964), submitted 2026-07-09, v2 2026-07-13

### [Towards Load-Aware Prefill Deflection for Disaggregated LLM Serving](https://arxiv.org/abs/2607.02043)
- Status: proposed — awaiting review
- Claim: On a production-style A100 cluster (2 prefill / 2 decode nodes), prefill compute accounts for only 2-23% of P95 Time-to-First-Token — queuing and inter-node KV-cache transfer dominate the rest; a proactive scheduler that lets decode nodes serve chunked-prefill steps interleaved with in-flight decode batches (within the decode SLO) cuts P95 TTFT by up to 81% and raises SLO attainment by up to 79% vs. state-of-the-art disaggregated schedulers, on DeepSeek-V2-Lite production-style traces.
- Why it matters: A scheduling/queueing-level serving-infra claim, distinct from the already-queued KV-cache-reuse/compression and speculative-decoding candidates — this is about request scheduling across disaggregated prefill/decode pools rather than cache or decode-algorithm changes.
- Testability: The full claim needs a real multi-GPU 2P2D cluster, out of budget for a personal setup. But the scheduling algorithm itself is testable as a CPU-only discrete-event simulation: synthesize a bursty, heavy-tailed request trace, model prefill/decode/KV-transfer costs analytically (calibrated to the paper's own numbers), and compare P95 TTFT/SLO attainment of baseline disaggregated scheduling vs. the deflection policy. No GPU, no API cost — effectively free. A real small-scale vLLM verification (2 small Modal GPU nodes for a few hours) would run roughly $15-25 and is a stretch on the budget; the simulation is the realistic first step.
- Source: arXiv cs.DC (2607.02043), submitted 2026-07-02 (Microsoft Azure Research)

### [jcode](https://github.com/1jehuang/jcode)
- Status: proposed — awaiting review
- Claim: GitHub-trending Rust project self-described as "the most intelligent agent harness for code" — 10,607 stars, +1,769 this week; no published benchmark numbers accompany the trending listing itself, so the claim is currently unverified marketing framing rather than a citable result.
- Why it matters: A fast-moving, real-world agent-harness implementation worth watching as a comparison point — if it documents a concrete session/context-structuring design, it would be a natural "does a popular real harness actually reduce cost or improve quality vs. naive" companion to this repo's own tested harnesses. Right now it's speculative.
- Testability: Low priority until it publishes concrete benchmark numbers or a design doc with a falsifiable claim — flagging only. If pursued later, would mean reading its source/docs to pin down an actual claim, then instrumenting it on a toy task vs. this repo's naive baseline, API-only, no GPU, rough cost $5-10 — but the claim needs to be identified first before a `/test-paper` run makes sense.
- Source: GitHub trending (rust/agent-framework), accessed 2026-07-22
