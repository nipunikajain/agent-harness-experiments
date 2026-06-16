"""Entrypoint for the agent-harness experiment: run(config, seed) -> metrics dict.

For one seed, it spins up a fresh workspace, runs the agent under the configured harness
strategy (naive vs structured — the single variable), grades the produced solution.py with
the shared objective grader, and returns metrics including the feature-pass count and the
token cost.

The agent model is the Anthropic API; ANTHROPIC_API_KEY must be set in the environment.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import yaml

from shared import agent, agent_eval

EXPERIMENT_DIR = Path(__file__).resolve().parent


def _load_features(n_features: int) -> list[dict]:
    data = yaml.safe_load((EXPERIMENT_DIR / "task" / "features.yaml").read_text())
    feats = data["features"][:n_features]
    # normalize whitespace in the folded specs
    return [{"id": f["id"], "name": f["name"], "spec": " ".join(f["spec"].split())} for f in feats]


def _make_client():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. This experiment bills the Anthropic API per token. "
            "Export a key (e.g. `export ANTHROPIC_API_KEY=sk-ant-...`) before running."
        )
    import anthropic

    return anthropic.Anthropic()


def run(config: dict, seed: int) -> dict:
    strategy_name = config["harness"]["strategy"]
    if strategy_name not in agent.STRATEGIES:
        raise ValueError(f"Unknown harness.strategy={strategy_name!r}")

    n_features = int(config["task"]["n_features"])
    features = _load_features(n_features)
    model = config["model"]

    # Fresh workspace per (arm, seed) so grading is never contaminated by a prior run.
    ws = EXPERIMENT_DIR / "results" / "_workspaces" / strategy_name / f"seed_{seed}"
    if ws.exists():
        shutil.rmtree(ws)
    ws.mkdir(parents=True, exist_ok=True)

    # Flatten the few config keys the agent loop expects.
    run_cfg = {
        "model": model,
        "temperature": float(config.get("temperature", 1.0)),
        "max_output_tokens": int(config.get("max_output_tokens", 4096)),
        "max_turns": int(config.get("max_turns", 40)),
        "max_turns_per_feature": int(config.get("max_turns_per_feature", 6)),
    }
    budget = agent.RunBudget(
        max_total_tokens=int(config["budget"]["max_total_tokens"]), model=model
    )

    client = _make_client()
    strategy = agent.STRATEGIES[strategy_name]
    info = strategy(client, ws, features, run_cfg, budget)

    grade = agent_eval.run_checks(ws, n_features)

    return {
        "strategy": strategy_name,
        "features_passed": grade["passed"],
        "features_total": grade["total"],
        "pass_rate": grade["passed"] / grade["total"] if grade["total"] else 0.0,
        "sessions": info["sessions"],
        "turns": info["turns"],
        "tokens_in": budget.input_tokens,
        "tokens_out": budget.output_tokens,
        "total_tokens": budget.total_tokens,
        "est_cost_usd": round(budget.est_cost_usd, 4),
        "budget_hit": budget.exhausted(),
    }
