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

## 2026-07-13 — proposed by research-scout

### [Stop Comparing LLM Agents Without Disclosing the Harness](https://arxiv.org/abs/2605.23950)
- Status: proposed — awaiting review
- Claim: Position/empirical paper arguing the "Binding Constraint Thesis": for long-horizon tasks among comparably-capable frontier models, harness-induced performance variance often exceeds model-induced variance (including cases of outright model-ranking reversal), so leaderboard comparisons that don't disclose harness configuration are incomplete/misleading; proposes a harness-aware evaluation framework with a disclosure standard and variance-decomposition protocol.
- Why it matters: Directly upstream of this repo's own scoreboard — all 3 tested harness-overhead experiments here already show harness choice swinging cost/quality outcomes dramatically. This paper gives a formal variance-decomposition method to quantify "how much of the variance is harness vs. model," reusable on the repo's own existing harness code.
- Testability: Cheap, API-only, and reuses existing repo assets. Run a small 2×2 (structured vs. naive harness, already built here) × (Haiku 4.5 vs. Sonnet 4.6) grid with a few seeds each on one toy task, then decompose variance (harness effect vs. model effect vs. interaction) the way the paper proposes. No GPU. Rough cost: $10-15.
- Source: arXiv cs.AI/cs.SE (2605.23950), submitted 2026-05-29

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
