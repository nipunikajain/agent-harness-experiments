"""A small, scripted coding-agent loop driven by the Anthropic API.

This is the reusable engine for the agent-harness experiment. It exposes:

  - a sandboxed toolset (write_file / read_file / list_files / run_tests) scoped to a
    per-run workspace directory,
  - a budget tracker with a HARD per-run token cap and an estimated-USD accountant, and
  - two harness *strategies* that are the single variable under study:
      * "naive"      — one session; the whole feature list dumped at once; work until done
                       or budget exhausted. Context (the full transcript) grows every turn.
      * "structured" — one feature per session; context is RESET to a compact state
                       (a progress log + current file listing) between features, emulating
                       the article's "incremental single-feature progress with clean,
                       documented state". Cheaper per turn, so more useful work per token.

Both arms get the same model, the same tools, and the same total token budget. Only the
strategy differs.

No credentials live here. The Anthropic client reads ANTHROPIC_API_KEY from the environment.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from shared import agent_eval

# Rough public list prices (USD per token), used only for the cost estimate / budget guard.
# Input, output. Update if prices change — this only affects the *estimate*, not the run.
MODEL_PRICING: dict[str, tuple[float, float]] = {
    "claude-sonnet-4-6": (3e-6, 15e-6),
    "claude-haiku-4-5-20251001": (1e-6, 5e-6),
    "claude-opus-4-5": (15e-6, 75e-6),
}


class RunBudget:
    """Tracks tokens for one (arm, seed) run and enforces a hard total-token ceiling."""

    def __init__(self, max_total_tokens: int, model: str):
        self.max_total_tokens = max_total_tokens
        self.model = model
        self.input_tokens = 0
        self.output_tokens = 0

    def add(self, usage: Any) -> None:
        self.input_tokens += int(getattr(usage, "input_tokens", 0) or 0)
        self.output_tokens += int(getattr(usage, "output_tokens", 0) or 0)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def est_cost_usd(self) -> float:
        cin, cout = MODEL_PRICING.get(self.model, (3e-6, 15e-6))
        return self.input_tokens * cin + self.output_tokens * cout

    def exhausted(self) -> bool:
        return self.total_tokens >= self.max_total_tokens


# --------------------------------------------------------------------------------------
# Sandboxed tools. All paths are confined to the run's workspace.
# --------------------------------------------------------------------------------------
def _safe_path(workspace: Path, rel: str) -> Path:
    p = (workspace / rel).resolve()
    if not str(p).startswith(str(workspace.resolve())):
        raise ValueError("path escapes workspace")
    return p


def make_tools(workspace: Path, n_features: int):
    workspace = Path(workspace)

    def write_file(path: str, content: str) -> str:
        p = _safe_path(workspace, path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return f"wrote {path} ({len(content)} bytes)"

    def read_file(path: str) -> str:
        p = _safe_path(workspace, path)
        if not p.exists():
            return f"(no such file: {path})"
        return p.read_text()

    def list_files() -> str:
        files = sorted(
            str(f.relative_to(workspace))
            for f in workspace.rglob("*")
            if f.is_file()
        )
        return "\n".join(files) if files else "(empty workspace)"

    def run_tests() -> str:
        result = agent_eval.run_checks(workspace, n_features)
        return agent_eval.summary_text(result)

    impls: dict[str, Callable] = {
        "write_file": lambda path, content: write_file(path, content),
        "read_file": lambda path: read_file(path),
        "list_files": lambda: list_files(),
        "run_tests": lambda: run_tests(),
    }

    schemas = [
        {
            "name": "write_file",
            "description": "Create or overwrite a file in the workspace.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path, e.g. solution.py"},
                    "content": {"type": "string", "description": "Full file contents."},
                },
                "required": ["path", "content"],
            },
        },
        {
            "name": "read_file",
            "description": "Read a file from the workspace.",
            "input_schema": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
        {
            "name": "list_files",
            "description": "List all files in the workspace.",
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "run_tests",
            "description": "Run the acceptance checks and see which features pass or fail.",
            "input_schema": {"type": "object", "properties": {}},
        },
    ]
    return schemas, impls


# --------------------------------------------------------------------------------------
# The core turn loop.
# --------------------------------------------------------------------------------------
def _run_session(
    client,
    model: str,
    system: str,
    messages: list[dict],
    schemas: list[dict],
    impls: dict[str, Callable],
    budget: RunBudget,
    max_turns: int,
    max_output_tokens: int,
    temperature: float,
) -> dict:
    """Drive one chat session until end_turn, max_turns, or budget exhaustion."""
    turns = 0
    for _ in range(max_turns):
        if budget.exhausted():
            break
        turns += 1
        resp = client.messages.create(
            model=model,
            max_tokens=max_output_tokens,
            system=system,
            messages=messages,
            tools=schemas,
            temperature=temperature,
        )
        budget.add(resp.usage)

        assistant_content: list[dict] = []
        tool_uses = []
        for block in resp.content:
            if block.type == "text":
                assistant_content.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                assistant_content.append(
                    {"type": "tool_use", "id": block.id, "name": block.name, "input": block.input}
                )
                tool_uses.append(block)
        messages.append({"role": "assistant", "content": assistant_content})

        if resp.stop_reason != "tool_use":
            break

        tool_results = []
        for tu in tool_uses:
            try:
                out = impls[tu.name](**(tu.input or {}))
            except Exception as e:  # surface tool errors to the model instead of crashing
                out = f"ERROR: {e}"
            tool_results.append(
                {"type": "tool_result", "tool_use_id": tu.id, "content": str(out)}
            )
        messages.append({"role": "user", "content": tool_results})

    return {"turns": turns}


# --------------------------------------------------------------------------------------
# Strategies — the single variable.
# --------------------------------------------------------------------------------------
_SHARED_RULES = (
    "You are a coding agent. You implement Python features in a file named solution.py in "
    "the workspace, using the provided tools. Write plain standard-library Python (no third-"
    "party imports). Use run_tests to check your work. When the targeted features pass, stop."
)


def run_naive(client, workspace, features, config, budget) -> dict:
    """One session, all features at once. Transcript grows every turn."""
    n = len(features)
    schemas, impls = make_tools(workspace, n)
    feature_block = "\n".join(f"- {f['id']} {f['name']}: {f['spec']}" for f in features)
    system = _SHARED_RULES
    user = (
        f"Implement ALL {n} of the following features in solution.py. Run the tests as you "
        f"go and fix failures until as many as possible pass.\n\nFEATURES:\n{feature_block}"
    )
    messages = [{"role": "user", "content": user}]
    info = _run_session(
        client, config["model"], system, messages, schemas, impls, budget,
        max_turns=config["max_turns"],
        max_output_tokens=config["max_output_tokens"],
        temperature=config["temperature"],
    )
    return {"sessions": 1, "turns": info["turns"]}


def run_structured(client, workspace, features, config, budget) -> dict:
    """One feature per session; context reset to a compact state between features."""
    workspace = Path(workspace)
    n = len(features)
    schemas, impls = make_tools(workspace, n)
    progress_path = workspace / "progress.md"
    progress_path.write_text("# Progress log\n")
    total_turns = 0
    sessions = 0

    for f in features:
        if budget.exhausted():
            break
        sessions += 1
        # Compact, "clean documented state": current files + progress log only — NOT the
        # full prior transcript. This is the article's mechanism.
        existing = sorted(p.name for p in workspace.glob("*.py"))
        solution_now = ""
        sol = workspace / "solution.py"
        if sol.exists():
            solution_now = sol.read_text()
        system = _SHARED_RULES
        user = (
            f"This is an incremental session. Implement EXACTLY ONE feature now, preserving "
            f"all previously working features in solution.py.\n\n"
            f"FEATURE TO ADD:\n- {f['id']} {f['name']}: {f['spec']}\n\n"
            f"Workspace files: {existing}\n"
            f"Progress log so far:\n{progress_path.read_text()}\n\n"
            f"Current solution.py:\n```python\n{solution_now}\n```\n\n"
            f"Add the feature, run_tests to confirm it (and prior features) pass, then stop."
        )
        messages = [{"role": "user", "content": user}]
        info = _run_session(
            client, config["model"], system, messages, schemas, impls, budget,
            max_turns=config["max_turns_per_feature"],
            max_output_tokens=config["max_output_tokens"],
            temperature=config["temperature"],
        )
        total_turns += info["turns"]
        # Append to the documented state for the next clean session.
        res = agent_eval.run_checks(workspace, n)
        with progress_path.open("a") as fh:
            fh.write(f"- attempted {f['id']} {f['name']}: now {res['passed']}/{res['total']} passing\n")

    return {"sessions": sessions, "turns": total_turns}


STRATEGIES = {"naive": run_naive, "structured": run_structured}
