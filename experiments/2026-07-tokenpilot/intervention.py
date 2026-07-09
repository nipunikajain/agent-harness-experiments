"""TokenPilot vs. Vanilla — cache-efficient context management for an LLM agent.

Entrypoint the shared runner calls: ``run(config, seed) -> metrics dict``. The single variable
under study is ``tokenpilot.enabled`` (baseline config sets it false; the intervention config
sets it true). Everything else — model, tasks, tools, seeds, prompt-caching setup — is identical
across the two conditions, so any difference in billed cost or accuracy is attributable to the
TokenPilot context-management framework and nothing else.

Both conditions use standard Anthropic prompt caching (a cache breakpoint on the static system+
tools prefix, plus a rolling breakpoint on the growing conversation). This is deliberate: the
baseline is a *competent* naive agent, not a strawman with caching switched off. On top of that
baseline, ``tokenpilot.enabled: true`` turns on the paper's three mechanisms:

  1. Prefix Stabilization  — the volatile per-task "Session" marker at the top of the system
     prompt is replaced by a static placeholder, so the (large) system+tools prefix is byte-
     identical across every task and is served from cache instead of re-written per task.
  2. Observation Reduction — raw tool observations (noisy HTML) are passed through the
     deterministic rule-based reducer in tasks.py before being appended to the context.
  3. Lifecycle-Aware Eviction — completed tool observations older than a keep-window are purged
     in batches of B turns.

Cost is computed from the API's own usage metadata (input / cache_creation / cache_read / output
token counts) at real Claude Haiku 4.5 prices — the same decomposition TokenPilot uses. The system
prompt is deliberately sized (~4.7k tokens) above Haiku 4.5's minimum cacheable-prefix length so
that prompt caching activates at all; production agent prompts are routinely this size or larger.
"""

from __future__ import annotations

import os
from pathlib import Path

import anthropic

import tasks
from shared.agent import Accountant, BudgetExceeded

# --- Real Claude Haiku 4.5 pricing, USD per token -------------------------------------
PRICE_INPUT = 1.00e-6         # uncached input
PRICE_OUTPUT = 5.00e-6        # output
PRICE_CACHE_WRITE = 1.25e-6   # 5-minute cache write (1.25x base input)
PRICE_CACHE_READ = 0.10e-6    # cache read (0.10x base input)


def _call_cost(u) -> float:
    return (
        int(getattr(u, "input_tokens", 0) or 0) * PRICE_INPUT
        + int(getattr(u, "cache_creation_input_tokens", 0) or 0) * PRICE_CACHE_WRITE
        + int(getattr(u, "cache_read_input_tokens", 0) or 0) * PRICE_CACHE_READ
        + int(getattr(u, "output_tokens", 0) or 0) * PRICE_OUTPUT
    )


# A deliberately substantial, static agent operating manual for the referral-chain task. It must
# exceed Haiku 4.5's minimum cacheable-prefix length (~4.1k tokens) for prompt caching to activate
# at all, which is why it is long — real production agent system prompts are this size or larger.
# Its content is genuine policy; none of it varies between the two conditions.
RULES = """You are a meticulous registry-tracing agent operating inside a private corporate
referral registry. Your job is to answer the user's question correctly by retrieving registry
records and following the referral chain they describe, then reporting a single final answer.

TOOLS AND HOW TO USE THEM
You have exactly three tools: open, recover, and submit_answer.
- open(doc_id): fetch a registry document by its id. Registry record ids follow a strict scheme of
  the form "record/<q>-<n>", where <q> is the question's chain number and <n> is a node index, both
  non-negative integers, joined by a single hyphen, with the literal prefix "record/". For example
  "record/2-0" and "record/2-3" are two records belonging to chain number 2. You will always be
  given the id of the first record in the question itself; every subsequent id you need is printed
  inside a record you have already opened, so you never have to invent one.
- recover(doc_id): fetch the FULL untrimmed document by the same id. Some documents you open may be
  returned in a condensed form to save space. If a condensed document appears to be missing the
  specific detail you need — the next-record pointer or the final destination city — call recover on
  that same id to retrieve the complete original text.
- submit_answer(answer): report your final answer and end the task. Provide ONLY the specific value
  requested: for these questions that is the destination city named in the final record, given as a
  bare city name with no surrounding sentence, punctuation, or explanation.

HOW A REFERRAL CHAIN WORKS
Each question describes a chain of registry records. The question gives you the id of the starting
record. When you open a record, its main content is one of two kinds. An intermediate record states
"Next record: record/<q>-<m>", naming the id of the following record in the chain. A final record
states "Final destination city: <City>" and explicitly notes that the chain ends there. Your job is
to start at the given record, read its "Next record" pointer, open that record, read its pointer,
and continue hop by hop until you reach the final record, whose destination city is the answer. The
pointer order is deliberately not the numeric id order, so you cannot shortcut the chain by guessing
sequential ids; you must actually open each record and read the pointer it contains.

STEP-BY-STEP STRATEGY
Work one hop at a time. Open the starting record named in the question. Locate the "Next record"
line in its main content and read the exact id it names. Open that id. Repeat. Each record tells you
either where to go next or that you have arrived. Do not open records that no pointer has directed
you to; the only valid ids to open are the starting id from the question and whatever id the current
record's pointer names. When you open a record whose main content says "Final destination city",
that value is your answer — submit it immediately and stop. Do not continue opening records after
you have reached the final one, and do not re-open records you have already read, because their
contents are already present earlier in your context and re-opening them only wastes retrieval.

READING DOCUMENTS
Registry records are internal web pages and contain navigation chrome, a cookie banner, inline
scripts, styling, breadcrumbs, and a legal footer in addition to their main content. The pointer or
destination you need is ALWAYS in the main content region of the page (the part headed "Registry
record ..."), never in the navigation, banner, breadcrumbs, or footer. Focus only on the main
content. If a document has been condensed to save space, its main content and its key line (the
"Next record" pointer or the "Final destination city") are preserved; only the surrounding chrome is
removed. Read the condensed main content carefully before concluding that anything is missing.

USING RECOVER SPARINGLY
The recover tool exists for the rare case where a condensed document genuinely does not contain the
pointer or destination you need. In the overwhelming majority of cases the condensed document retains
exactly the line you are looking for, so calling recover is unnecessary and wasteful: it re-introduces
the very page chrome that was trimmed for good reason and increases the amount of text you must read.
Reserve recover for the specific situation where the key line is truly absent from the condensed form.
When you do recover a document, read only its main content region and ignore all chrome.

EFFICIENCY AND CARE
Be efficient. Open exactly the records the chain directs you to, in order, and no others. Do not open
records speculatively, do not open the same record twice, and do not open records belonging to a
different chain number than the one in your question. Keep your intermediate reasoning short and
purposeful; a brief note of which id you are about to open and why is enough. The number of hops is
modest, so a correct trajectory is simply: open, read pointer, open, read pointer, ..., open, read
destination, submit. Aim to reach the destination with the minimum number of open calls, which equals
the number of records in the chain.

ACCURACY REQUIREMENTS
Your answer is graded by exact match against the ground-truth destination city, so precision matters.
Copy the city exactly as it appears in the final record's main content. Do not add explanations,
punctuation, or extra words to your final answer — submit the bare city name. If you are ever unsure
whether you have reached the final record, check whether its main content says "Next record" (keep
going) or "Final destination city" (stop and submit). Never submit a city that you have not actually
seen printed as the destination in a final record, and never fabricate a pointer or a city.

OPERATING PRINCIPLES
Stay strictly within the tools provided; you cannot browse the public internet or run code. Treat
every registry record as authoritative internal data. Do not speculate about information that is not
in the records you have retrieved. Maintain a clear chain of reasoning from the starting record,
through each pointer you follow, to the destination city you submit. Prefer the smallest number of
tool calls that reliably yields the correct answer. Remember that record ids are case-sensitive and
must be used exactly as printed, and that the fastest correct path is to follow each pointer directly
without detours.

WORKED EXAMPLE
Suppose the question says the chain begins at "record/0-2". You open "record/0-2" and its main content
reads "Next record: record/0-0." You open "record/0-0" and it reads "Next record: record/0-3." You
open "record/0-3" and it reads "Next record: record/0-1." You open "record/0-1" and it reads "Final
destination city: Bergen." You then call submit_answer with exactly "Bergen" and stop. Note how you
followed the pointers in the order the records dictated (2, 0, 3, 1) rather than numeric order, opened
each record exactly once, did not call recover because each condensed record already contained its
key line, and submitted only the bare city name. That is the ideal trajectory: one open per record in
the chain, one submit, and no wasted retrieval or recovery.

FAILURE MODES TO AVOID
Do not answer from memory or prior knowledge; the only valid source is the records you retrieve in
this task. Do not guess the next id from numeric order — always read the printed "Next record" line.
Do not confuse a chain with another chain: every id in your chain shares the same <q> number as your
starting id. Do not include multiple candidate cities in your final answer — commit to the one printed
in the final record. Do not keep opening records after you have reached the final one; additional tool
calls cost time and add nothing. Do not invent record ids that no pointer has named. If a tool reports
that no such document exists, re-read the pointer you copied and correct any deviation from the exact
id before trying again.

=== REGISTRY REFERENCE (static) ===
The following reference describes the referral registry you operate over. It is stable context: it
never changes between tasks, which is exactly why a well-engineered agent keeps it at the front of the
prompt where it can be served from cache rather than re-sent on every request.

RECORD ANATOMY
Every registry record is a single internal web page with a stable structure. Outside the main content
region it carries a fixed navigation bar linking to the home page, the directory, the records index,
help, system status, and sign-in; a breadcrumb trail; a cookie-consent banner describing the site's
use of cookies and preference management; a block of inline styling; and a legal footer stating the
copyright, the terms of service, the privacy policy, the acceptable-use policy, the data-retention
schedule, a confidentiality notice, and guidance to return to the directory if the page was reached in
error. None of that chrome ever contains routing data. Inside the main content region, headed
"Registry record record/<q>-<n>", the page states a short status line ("Status: active. Verified:
yes."), then the one line that matters — either a "Next record" pointer to the following id, or a
"Final destination city" naming the chain's destination — followed by a routine data-hygiene note.

IDENTIFIER CONVENTIONS
Record ids are formed as the literal prefix "record/" followed by the chain number, a hyphen, and the
node index, with no spaces, no uppercase letters, and no trailing characters. The chain number groups
all records that belong to one question; the node index distinguishes records within that chain but
does NOT indicate their order in the chain, which is defined solely by the pointers. When you copy an
id from a "Next record" line, reproduce it exactly, including both numbers and the single separating
hyphen; a one-character deviation will cause open to report that no such document exists.

FIELD GLOSSARY
"Next record" denotes the id of the following hop in the chain and appears only on intermediate
records. "Final destination city" denotes the answer and appears only on the final record; it is the
value you submit. "Status" and "Verified" are descriptive metadata and are never the target of a
question. Treat any value appearing in navigation, breadcrumbs, the cookie banner, styling, inline
scripts, or the footer as chrome, never as routing data; the pointer and the destination live only in
the main content region.

RETRIEVAL AND CONDENSED-CONTENT POLICY
Retrieve the minimum set of records that answers the question: exactly the records on the chain, each
opened once, in pointer order. Retrieving any other record is a signal you have left the direct path;
pause and reconsider before doing so. To conserve space, records you open may be delivered in a
condensed representation that preserves the heading and the key line ("Next record" or "Final
destination city") while trimming the surrounding chrome and prose. This condensed representation is
authoritative for the line it retains. Only when the specific line you need is genuinely absent from
the condensed representation should you fall back to recover, which returns the untrimmed original.
Habitually calling recover defeats the purpose of condensation and should be avoided.

ESCALATION AND UNCERTAINTY
If, after following the chain to what appears to be its final record, you still cannot locate a
"Final destination city" line, first re-read the condensed main content you already hold, and only
then, if the line is truly absent, recover the full document. Uncertainty is not license to invent a
city; it is a signal to re-read the records you already have before concluding. In all cases end the
task with exactly one submit_answer call carrying the bare destination city and nothing else.

EXTENDED OPERATIONAL NOTES
The registry is designed so that a disciplined agent can always reach the destination with a
predictable, minimal trajectory, and the notes below exist to keep you on that trajectory even in the
presence of the surrounding page chrome. First, treat the starting id in the question as authoritative
and open it verbatim; do not normalize, reorder, or reinterpret it. Second, when you read a "Next
record" line, copy the id it names exactly as printed, character for character, including both the
chain number and the node index and the single hyphen that separates them, and open precisely that id
next. Third, never assume that the node indices increase or decrease along the chain; the registry
deliberately randomizes node order within a chain so that only the pointers define the sequence, and
any attempt to shortcut by opening ids in numeric order will lead you off the chain. Fourth, keep a
brief running note to yourself of which ids you have already opened, so that you never open the same
record twice and never lose your place in the chain. Fifth, recognize the two terminal signals: a
record that contains a "Next record" line is an intermediate hop and you must continue, whereas a
record that contains a "Final destination city" line is the terminus and you must stop and submit.

COST AND CONTEXT DISCIPLINE
Although you should never sacrifice correctness for brevity, you should also avoid actions that add
cost without adding information. Re-opening a record you have already read adds a large block of text
to your context for no new information, because the pointer or destination it contains is already in
your earlier messages. Calling recover on a condensed record that already shows the line you need adds
back the page chrome that was deliberately trimmed, again for no new information. Opening records that
no pointer directed you to wastes retrieval and risks confusing one chain with another. Each of these
actions makes your context longer and your trajectory more expensive while bringing you no closer to
the answer, so avoid them. The disciplined pattern — open the starting record, follow each pointer
exactly once, stop at the terminus, and submit the bare city — is both the cheapest and the most
reliable path, and it is the pattern you should follow on every question without exception.

INTERPRETING CONDENSED RECORDS IN DETAIL
When observation reduction is in effect, an opened record is delivered to you as a compact line of
text that preserves the record heading and the single routing line while omitting the navigation bar,
breadcrumb trail, cookie banner, styling, inline scripts, and legal footer. In this compact form the
"Next record" pointer or the "Final destination city" appears in the same words as in the full page,
so you can read it directly and proceed. Do not be alarmed by the absence of the surrounding chrome;
its absence is intentional and never removes routing information. If, in a genuinely exceptional case,
the compact form does not contain a routing line at all — neither a pointer nor a destination — then
and only then should you call recover on that id and read the routing line from the full page, again
ignoring all of the chrome. This situation should essentially never arise in normal operation, and if
you find yourself reaching for recover on most records, you are misreading the compact form; slow down
and read the compact main content, which does contain the line you need.

SUMMARY OF THE CONTRACT
To summarize the operating contract one final time: you receive a question naming a starting registry
record; you open that record and read its routing line; if the routing line is a pointer you open the
named record next, and you repeat this until a record's routing line is a destination city; you then
submit that city as a bare value and stop. You use open for normal retrieval, recover only for the
rare condensed record missing its routing line, and submit_answer exactly once at the end. You read
only the main content of each record, you follow only the pointers the records give you, you open each
record on the chain exactly once, and you never invent ids, cities, or pointers. Adhering to this
contract yields the correct destination city on every question at the lowest possible cost."""


# --------------------------------------------------------------------------------------
# Tool schemas (identical for both conditions).
# --------------------------------------------------------------------------------------
TOOL_SCHEMAS = [
    {"name": "open", "description": "Fetch a registry record by id (record/<q>-<n>).",
     "input_schema": {"type": "object", "properties": {"doc_id": {"type": "string"}},
                      "required": ["doc_id"]}},
    {"name": "recover", "description": "Fetch the FULL untrimmed original record by id (use only if "
                                       "a condensed record is missing the pointer or destination).",
     "input_schema": {"type": "object", "properties": {"doc_id": {"type": "string"}},
                      "required": ["doc_id"]}},
    {"name": "submit_answer", "description": "Report the final destination city and end the task.",
     "input_schema": {"type": "object", "properties": {"answer": {"type": "string"}},
                      "required": ["answer"]}},
]


def _load_api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    env = Path(__file__).resolve().parents[2] / ".env"  # repo-root .env (never committed)
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("ANTHROPIC_API_KEY="):
                return line.split("=", 1)[1].strip()
    raise RuntimeError("ANTHROPIC_API_KEY not found in env or repo-root .env")


def _system_blocks(session_id: str, cache: bool = True) -> list[dict]:
    """System prompt = a volatile 'Session' marker + the static rules, with a cache breakpoint.

    In the baseline the marker changes per task, so the whole prefix busts the cache each task.
    Under TokenPilot the marker is a static placeholder, so the prefix is identical across tasks and
    is served from cache. cache_control on the (single) block caches system + tools together. When
    `cache` is False (the no-cache "Vanilla" reference arm), no breakpoint is set at all.
    """
    block = {"type": "text", "text": f"Session: {session_id}\n\n{RULES}"}
    if cache:
        block["cache_control"] = {"type": "ephemeral"}
    return [block]


def _set_rolling_cache_breakpoint(messages: list[dict]) -> None:
    """Keep exactly one rolling cache breakpoint on the last content block of the last message,
    clearing any previous message-level breakpoints (Anthropic allows only a few)."""
    for msg in messages:
        content = msg.get("content")
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    block.pop("cache_control", None)
    last = messages[-1]["content"]
    if isinstance(last, list) and last and isinstance(last[-1], dict):
        last[-1]["cache_control"] = {"type": "ephemeral"}


def _evict(messages: list[dict], keep_last: int) -> None:
    """Lifecycle-aware eviction: replace the content of tool_result blocks older than the most
    recent `keep_last` of them with a compact stub. Conservative and idempotent."""
    positions = [
        (mi, bi)
        for mi, msg in enumerate(messages)
        if isinstance(msg.get("content"), list)
        for bi, b in enumerate(msg["content"])
        if isinstance(b, dict) and b.get("type") == "tool_result"
    ]
    drop = positions[:-keep_last] if keep_last else positions
    for mi, bi in drop:
        block = messages[mi]["content"][bi]
        if not str(block.get("content", "")).startswith("[evicted"):
            block["content"] = "[evicted: earlier record no longer in context; use recover()]"


def _run_task(client, model, docs, question, cfg, tp_enabled, session_id, budget, totals):
    """Drive one question to completion. Mutates `totals` (token/cost accumulators). Returns
    (correct: bool, turns: int, budget_hit: bool)."""
    messages = [{"role": "user", "content": [{"type": "text", "text": question["prompt"]}]}]
    submitted = None
    turns = 0
    for _ in range(cfg["max_turns"]):
        turns += 1
        if cfg["caching"]:
            _set_rolling_cache_breakpoint(messages)
        try:
            resp = client.messages.create(
                model=model, max_tokens=cfg["max_output_tokens"],
                system=_system_blocks(session_id, cache=cfg["caching"]), tools=TOOL_SCHEMAS,
                messages=messages, temperature=cfg["temperature"],
            )
        except anthropic.APIError as e:  # transient API failure: stop this task, keep the run
            totals["api_errors"] += 1
            print(f"[api-error {e.__class__.__name__}] ", end="")
            break

        u = resp.usage
        totals["input_tokens"] += int(getattr(u, "input_tokens", 0) or 0)
        totals["cache_write_tokens"] += int(getattr(u, "cache_creation_input_tokens", 0) or 0)
        totals["cache_read_tokens"] += int(getattr(u, "cache_read_input_tokens", 0) or 0)
        totals["output_tokens"] += int(getattr(u, "output_tokens", 0) or 0)
        try:
            budget.charge(_call_cost(u))  # file-backed USD kill switch, spans all seeds/configs
        except BudgetExceeded:
            return (False, turns, True)

        assistant_content, tool_uses = [], []
        for block in resp.content:
            if block.type == "text":
                assistant_content.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                assistant_content.append({"type": "tool_use", "id": block.id,
                                          "name": block.name, "input": block.input})
                tool_uses.append(block)
        messages.append({"role": "assistant", "content": assistant_content})

        if resp.stop_reason != "tool_use":
            break  # model stopped without a tool call; no answer submitted

        tool_results = []
        for tu in tool_uses:
            name, args = tu.name, (tu.input or {})
            if name == "submit_answer":
                submitted = str(args.get("answer", ""))
                out = "Answer recorded. Task complete."
            elif name in ("open", "recover"):
                if name == "recover":
                    totals["recover_calls"] += 1
                raw = docs.get(str(args.get("doc_id", "")), f"(no such document: {args.get('doc_id')})")
                # Observation reduction is applied by the harness at the ingestion gate, and only for
                # `open` under TokenPilot. `recover` always returns the full document.
                if name == "open" and tp_enabled and raw.startswith("<!doctype"):
                    out = tasks.reduce_observation(raw, max_chars=cfg["reduce_max_chars"])
                else:
                    out = raw
            else:
                out = f"ERROR: unknown tool {name}"
            tool_results.append({"type": "tool_result", "tool_use_id": tu.id, "content": out})
        messages.append({"role": "user", "content": tool_results})

        if submitted is not None:
            break
        if tp_enabled and turns % cfg["evict_batch_turns"] == 0:
            _evict(messages, keep_last=cfg["evict_keep_last"])

    return (tasks.grade(submitted, question["answer"]), turns, False)


def run(config: dict, seed: int) -> dict:
    tp_cfg = config.get("tokenpilot", {})
    tp_enabled = bool(tp_cfg.get("enabled", False))
    model = config["model"]
    cfg = {
        "max_turns": int(config.get("max_turns", 10)),
        "max_output_tokens": int(config.get("max_output_tokens", 512)),
        "temperature": float(config.get("temperature", 0.0)),
        "reduce_max_chars": int(tp_cfg.get("reduce_max_chars", 600)),
        "evict_batch_turns": int(tp_cfg.get("evict_batch_turns", 3)),
        "evict_keep_last": int(tp_cfg.get("evict_keep_last", 2)),
        # Prompt caching on by default; the no-cache "Vanilla" reference arm sets it false.
        "caching": bool(config.get("caching", {}).get("enabled", True)),
    }

    client = anthropic.Anthropic(api_key=_load_api_key())
    docs, questions = tasks.build_world(
        seed, n_questions=int(config.get("n_questions", 5)),
        chain_len=int(config.get("chain_len", 4)))

    # File-backed USD kill switch shared across every seed and both configs of this experiment.
    ledger = Path(__file__).resolve().parent / "results" / ".spend_ledger.json"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    budget = Accountant(ledger, usd_cap=float(config.get("usd_cap", 4.5)))

    totals = {"input_tokens": 0, "cache_write_tokens": 0, "cache_read_tokens": 0,
              "output_tokens": 0, "api_errors": 0, "recover_calls": 0}
    correct = 0
    total_turns = 0
    budget_hit = False
    n_done = 0
    for q in questions:
        # Volatile session marker: changes per task in the baseline; static under TokenPilot.
        session_id = ("STATIC-AGENT-V1" if tp_enabled
                      else f"sess-{seed}-{q['id']}-{(hash(q['id']) & 0xffff)}")
        ok, turns, hit = _run_task(client, model, docs, q, cfg, tp_enabled, session_id, budget, totals)
        n_done += 1
        correct += int(ok)
        total_turns += turns
        if hit:
            budget_hit = True
            print("[budget cap hit — stopping] ", end="")
            break

    cost = (totals["input_tokens"] * PRICE_INPUT
            + totals["cache_write_tokens"] * PRICE_CACHE_WRITE
            + totals["cache_read_tokens"] * PRICE_CACHE_READ
            + totals["output_tokens"] * PRICE_OUTPUT)
    total_input = totals["input_tokens"] + totals["cache_write_tokens"] + totals["cache_read_tokens"]
    cache_hit_rate = (totals["cache_read_tokens"] / total_input) if total_input else 0.0

    return {
        "tokenpilot": 1.0 if tp_enabled else 0.0,
        "accuracy": correct / n_done if n_done else 0.0,
        "n_tasks": float(n_done),
        "cost_usd": cost,
        "cost_usd_per_task": cost / n_done if n_done else 0.0,
        "cache_hit_rate": cache_hit_rate,
        "input_tokens": float(totals["input_tokens"]),
        "cache_write_tokens": float(totals["cache_write_tokens"]),
        "cache_read_tokens": float(totals["cache_read_tokens"]),
        "output_tokens": float(totals["output_tokens"]),
        "avg_turns": total_turns / n_done if n_done else 0.0,
        "recover_calls": float(totals["recover_calls"]),
        "api_errors": float(totals["api_errors"]),
        "budget_hit": 1.0 if budget_hit else 0.0,
    }
