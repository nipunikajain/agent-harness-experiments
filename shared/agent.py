"""A small, scripted coding-agent loop driven by the Anthropic API.

Reusable engine for the agent-harness experiments. Provides:
  - a sandboxed toolset (write_file / read_file / list_files / run_tests) scoped to a
    per-run workspace, graded by a pluggable `grader` module,
  - per-run token budgeting AND a process-spanning, file-backed USD kill-switch, so a
    multi-run sweep physically cannot exceed a hard dollar cap,
  - peak-vs-final pass tracking (for measuring regressions), and
  - two harness strategies that are the single variable under study:
      * "naive"      — one session; whole feature list at once; transcript grows every turn.
      * "structured" — one feature per session; context reset to a compact documented state
                       (progress log + current file) between features.

No credentials live here. The Anthropic client reads ANTHROPIC_API_KEY from the environment.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from shared import agent_eval  # default grader (utility-function task)

MODEL_PRICING: dict[str, tuple[float, float]] = {  # USD per token (input, output) — estimate
    "claude-sonnet-4-6": (3e-6, 15e-6),
    "claude-haiku-4-5-20251001": (1e-6, 5e-6),
    "claude-opus-4-5": (15e-6, 75e-6),
}


def price(model: str) -> tuple[float, float]:
    return MODEL_PRICING.get(model, (3e-6, 15e-6))


# --------------------------------------------------------------------------------------
# Hard USD kill-switch, persisted to a file so it spans every run in a sweep.
# --------------------------------------------------------------------------------------
class BudgetExceeded(Exception):
    pass


class Accountant:
    def __init__(self, ledger_path: Path, usd_cap: float):
        self.ledger_path = Path(ledger_path)
        self.usd_cap = usd_cap
        if not self.ledger_path.exists():
            self.ledger_path.write_text(json.dumps({"spent_usd": 0.0}))

    def spent(self) -> float:
        try:
            return float(json.loads(self.ledger_path.read_text())["spent_usd"])
        except Exception:
            return 0.0

    def remaining(self) -> float:
        return max(0.0, self.usd_cap - self.spent())

    def charge(self, usd: float) -> None:
        total = self.spent() + usd
        self.ledger_path.write_text(json.dumps({"spent_usd": total}))
        if total > self.usd_cap:
            raise BudgetExceeded(f"USD cap ${self.usd_cap:.2f} exceeded (spent ${total:.4f})")


_ACCOUNTANT: Accountant | None = None


def set_accountant(acc: Accountant | None) -> None:
    global _ACCOUNTANT
    _ACCOUNTANT = acc


class RunBudget:
    """Per-run token tracker; also charges the global USD accountant as tokens accrue."""

    def __init__(self, max_total_tokens: int, model: str):
        self.max_total_tokens = max_total_tokens
        self.model = model
        self.input_tokens = 0
        self.output_tokens = 0

    def add(self, usage) -> None:
        din = int(getattr(usage, "input_tokens", 0) or 0)
        dout = int(getattr(usage, "output_tokens", 0) or 0)
        self.input_tokens += din
        self.output_tokens += dout
        if _ACCOUNTANT is not None:
            cin, cout = price(self.model)
            _ACCOUNTANT.charge(din * cin + dout * cout)  # may raise BudgetExceeded

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def est_cost_usd(self) -> float:
        cin, cout = price(self.model)
        return self.input_tokens * cin + self.output_tokens * cout

    def exhausted(self) -> bool:
        return self.total_tokens >= self.max_total_tokens


# --------------------------------------------------------------------------------------
# Sandboxed tools.
# --------------------------------------------------------------------------------------
def _safe_path(workspace: Path, rel: str) -> Path:
    p = (workspace / rel).resolve()
    if not str(p).startswith(str(workspace.resolve())):
        raise ValueError("path escapes workspace")
    return p


def make_tools(workspace: Path, n_features: int, grader=agent_eval):
    workspace = Path(workspace)

    def write_file(path: str, content: str) -> str:
        p = _safe_path(workspace, path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return f"wrote {path} ({len(content)} bytes)"

    def append_file(path: str, content: str) -> str:
        p = _safe_path(workspace, path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a") as fh:
            fh.write(content)
        return f"appended {len(content)} bytes to {path}"

    def read_file(path: str) -> str:
        p = _safe_path(workspace, path)
        return p.read_text() if p.exists() else f"(no such file: {path})"

    def list_files() -> str:
        files = sorted(str(f.relative_to(workspace)) for f in workspace.rglob("*") if f.is_file())
        return "\n".join(files) if files else "(empty workspace)"

    def run_tests() -> str:
        return grader.summary_text(grader.run_checks(workspace, n_features))

    impls: dict[str, Callable] = {
        "write_file": lambda path, content: write_file(path, content),
        "append_file": lambda path, content: append_file(path, content),
        "read_file": lambda path: read_file(path),
        "list_files": lambda: list_files(),
        "run_tests": lambda: run_tests(),
    }
    schemas = [
        {"name": "write_file", "description": "Create or overwrite a file in the workspace.",
         "input_schema": {"type": "object", "properties": {
             "path": {"type": "string"}, "content": {"type": "string"}},
             "required": ["path", "content"]}},
        {"name": "append_file", "description": "Append text to the end of a file (for building a large file in pieces).",
         "input_schema": {"type": "object", "properties": {
             "path": {"type": "string"}, "content": {"type": "string"}},
             "required": ["path", "content"]}},
        {"name": "read_file", "description": "Read a file from the workspace.",
         "input_schema": {"type": "object", "properties": {"path": {"type": "string"}},
                          "required": ["path"]}},
        {"name": "list_files", "description": "List all files in the workspace.",
         "input_schema": {"type": "object", "properties": {}}},
        {"name": "run_tests", "description": "Run the acceptance checks; see which features pass/fail.",
         "input_schema": {"type": "object", "properties": {}}},
    ]
    return schemas, impls


def _passed(grader, workspace, n_features) -> int:
    try:
        return grader.run_checks(workspace, n_features)["passed"]
    except Exception:
        return 0


# --------------------------------------------------------------------------------------
# Core turn loop.
# --------------------------------------------------------------------------------------
def _run_session(client, model, system, messages, schemas, impls, budget, max_turns,
                 max_output_tokens, temperature, grader, workspace, n_features, peak):
    """Drive one chat session. Tracks peak passes in `peak` (a 1-element list). Returns turns."""
    turns = 0
    for _ in range(max_turns):
        if budget.exhausted():
            break
        turns += 1
        try:
            resp = client.messages.create(
                model=model, max_tokens=max_output_tokens, system=system,
                messages=messages, tools=schemas, temperature=temperature,
            )
            budget.add(resp.usage)
        except BudgetExceeded:
            raise
        assistant_content, tool_uses = [], []
        for block in resp.content:
            if block.type == "text":
                assistant_content.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                assistant_content.append({"type": "tool_use", "id": block.id,
                                          "name": block.name, "input": block.input})
                tool_uses.append(block)

        # Output truncated mid-message: the trailing tool_use is incomplete and unusable.
        # Keep only the text, nudge the model to continue in smaller pieces, and loop —
        # do NOT silently drop the turn (that would falsely zero a one-shot attempt).
        if resp.stop_reason == "max_tokens":
            text_only = [b for b in assistant_content if b["type"] == "text"] or \
                        [{"type": "text", "text": "(continuing)"}]
            messages.append({"role": "assistant", "content": text_only})
            messages.append({"role": "user", "content": (
                "Your previous message was cut off because it was too long. Continue. Build "
                "solution.py in smaller steps: write_file for the first chunk, then append_file "
                "to add more. Keep each individual tool call well under ~150 lines.")})
            continue

        messages.append({"role": "assistant", "content": assistant_content})

        if resp.stop_reason != "tool_use":
            break
        tool_results = []
        for tu in tool_uses:
            try:
                out = impls[tu.name](**(tu.input or {}))
            except Exception as e:
                out = f"ERROR: {e}"
            tool_results.append({"type": "tool_result", "tool_use_id": tu.id, "content": str(out)})
        messages.append({"role": "user", "content": tool_results})
        peak[0] = max(peak[0], _passed(grader, workspace, n_features))  # catch intra-session regressions
    return turns


_SHARED_RULES = (
    "You are a coding agent. You implement a Python file named solution.py in the workspace "
    "using the provided tools. Write plain standard-library Python (no third-party imports). "
    "If solution.py is large, build it across multiple tool calls: write_file for the first "
    "chunk, then append_file for the rest, keeping each call well under ~150 lines so it is "
    "never truncated. Use run_tests to check your work. When the targeted features pass, stop."
)


def run_naive(client, workspace, features, config, budget, grader=agent_eval) -> dict:
    n = len(features)
    schemas, impls = make_tools(workspace, n, grader)
    feature_block = "\n".join(f"- {f['id']} {f['name']}: {f['spec']}" for f in features)
    user = (config.get("task_preamble", "") +
            f"\nImplement ALL {n} of the following features in solution.py. Run the tests as you "
            f"go and fix failures until as many as possible pass.\n\nFEATURES:\n{feature_block}")
    messages = [{"role": "user", "content": user}]
    peak = [0]
    try:
        turns = _run_session(client, config["model"], _SHARED_RULES, messages, schemas, impls,
                             budget, config["max_turns"], config["max_output_tokens"],
                             config["temperature"], grader, workspace, n, peak)
    except BudgetExceeded:
        turns = -1  # ran out of money mid-session
    return {"sessions": 1, "turns": turns, "peak_passed": peak[0]}


def run_structured(client, workspace, features, config, budget, grader=agent_eval) -> dict:
    workspace = Path(workspace)
    n = len(features)
    schemas, impls = make_tools(workspace, n, grader)
    progress_path = workspace / "progress.md"
    progress_path.write_text("# Progress log\n")
    total_turns, sessions = 0, 0
    peak = [0]
    try:
        for f in features:
            if budget.exhausted():
                break
            sessions += 1
            existing = sorted(p.name for p in workspace.glob("*.py"))
            sol = workspace / "solution.py"
            solution_now = sol.read_text() if sol.exists() else ""
            user = (config.get("task_preamble", "") +
                    f"\nThis is an incremental session. Implement EXACTLY ONE feature now, "
                    f"preserving all previously working features in solution.py.\n\n"
                    f"FEATURE TO ADD:\n- {f['id']} {f['name']}: {f['spec']}\n\n"
                    f"Workspace files: {existing}\n"
                    f"Progress log so far:\n{progress_path.read_text()}\n\n"
                    f"Current solution.py:\n```python\n{solution_now}\n```\n\n"
                    f"Add the feature, run_tests to confirm it (and prior features) pass, then stop.")
            messages = [{"role": "user", "content": user}]
            total_turns += _run_session(
                client, config["model"], _SHARED_RULES, messages, schemas, impls, budget,
                config["max_turns_per_feature"], config["max_output_tokens"],
                config["temperature"], grader, workspace, n, peak)
            res = grader.run_checks(workspace, n)
            peak[0] = max(peak[0], res["passed"])
            with progress_path.open("a") as fh:
                fh.write(f"- attempted {f['id']} {f['name']}: now {res['passed']}/{res['total']} passing\n")
    except BudgetExceeded:
        total_turns = -1
    return {"sessions": sessions, "turns": total_turns, "peak_passed": peak[0]}


STRATEGIES = {"naive": run_naive, "structured": run_structured}
