"""Reproducible experiment runner.

Given an experiment folder and its ``config.yaml``, run the entrypoint across every seed,
record everything needed to reproduce the run, and write timestamped results + a mean±std
summary. Print a comparison table to stdout.

    python -m shared.runner --experiment experiments/example-lr-sweep [--config config.yaml]

Contract: the experiment exposes ``run(config, seed) -> dict[str, float]`` (by default in
``intervention.py``). Backend (local vs Modal GPU) is selected by ``compute.backend`` in the
config; the runner itself is identical either way.
"""

from __future__ import annotations

import argparse
import json
import math
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from shared import modal_runner
from shared.seeds import set_all_seeds


# --------------------------------------------------------------------------------------
# Provenance: capture exactly what would be needed to reproduce this run.
# --------------------------------------------------------------------------------------
def _git(*args: str, cwd: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def git_provenance(cwd: Path) -> dict[str, Any]:
    commit = _git("rev-parse", "HEAD", cwd=cwd)
    status = _git("status", "--porcelain", cwd=cwd)
    return {
        "commit": commit,
        # dirty == there are uncommitted changes (or we couldn't determine, treated as unknown)
        "dirty": (bool(status) if status is not None else None),
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD", cwd=cwd),
    }


def pip_freeze() -> list[str]:
    try:
        out = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip().splitlines()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def build_manifest(config: dict, seeds: list[int], cwd: Path) -> dict[str, Any]:
    return {
        "resolved_config": config,
        "seeds": seeds,
        "git": git_provenance(cwd),
        "python_version": sys.version,
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "pip_freeze": pip_freeze(),
    }


# --------------------------------------------------------------------------------------
# Summary statistics over seeds.
# --------------------------------------------------------------------------------------
def _mean_std(values: list[float]) -> dict[str, float]:
    n = len(values)
    mean = sum(values) / n
    # population std (ddof=0); switch to sample std if you prefer.
    var = sum((v - mean) ** 2 for v in values) / n
    return {"mean": mean, "std": math.sqrt(var), "n": n}


def summarize(per_seed: dict[int, dict[str, Any]]) -> dict[str, dict[str, float]]:
    """Mean±std per metric, across seeds. Only numeric metrics are summarized."""
    metric_names: list[str] = []
    for metrics in per_seed.values():
        for k in metrics:
            if k not in metric_names:
                metric_names.append(k)

    summary: dict[str, dict[str, float]] = {}
    for name in metric_names:
        values = [
            float(per_seed[s][name])
            for s in per_seed
            if name in per_seed[s] and _is_number(per_seed[s][name])
        ]
        if values:
            summary[name] = _mean_std(values)
    return summary


def _is_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


# --------------------------------------------------------------------------------------
# Pretty stdout table.
# --------------------------------------------------------------------------------------
def _fmt(x: Any) -> str:
    if _is_number(x):
        return f"{x:.6g}"
    return str(x)


def print_comparison_table(
    per_seed: dict[int, dict[str, Any]], summary: dict[str, dict[str, float]]
) -> None:
    metric_names = list(summary.keys())
    # include any non-numeric metrics too, so nothing is silently dropped from the view
    for metrics in per_seed.values():
        for k in metrics:
            if k not in metric_names:
                metric_names.append(k)

    header = ["seed", *metric_names]
    rows = [header]
    for seed in sorted(per_seed):
        rows.append([str(seed)] + [_fmt(per_seed[seed].get(m, "—")) for m in metric_names])

    # mean±std footer row (only meaningful for numeric metrics)
    footer = ["mean±std"]
    for m in metric_names:
        if m in summary:
            footer.append(f"{summary[m]['mean']:.6g} ± {summary[m]['std']:.3g}")
        else:
            footer.append("—")
    rows.append(footer)

    widths = [max(len(r[i]) for r in rows) for i in range(len(header))]

    def render(row: list[str]) -> str:
        return "  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row))

    sep = "  ".join("-" * w for w in widths)
    print(render(rows[0]))
    print(sep)
    for row in rows[1:-1]:
        print(render(row))
    print(sep)
    print(render(rows[-1]))


# --------------------------------------------------------------------------------------
# Orchestration.
# --------------------------------------------------------------------------------------
def run_experiment(experiment_dir: Path, config_name: str = "config.yaml") -> dict[str, Any]:
    experiment_dir = Path(experiment_dir).resolve()
    config_path = experiment_dir / config_name
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    config = yaml.safe_load(config_path.read_text()) or {}
    seeds = config.get("seeds", [0, 1, 2])
    backend = config.get("compute", {}).get("backend", "local")

    results_dir = experiment_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    print(
        f"Running '{experiment_dir.name}' | config={config_name} | "
        f"backend={backend} | seeds={seeds}\n"
    )

    per_seed: dict[int, dict[str, Any]] = {}
    for seed in seeds:
        # Seed here for the local case (and any data prep the runner might do); the dispatch
        # layer also re-seeds immediately before the entrypoint, including on Modal.
        set_all_seeds(seed)
        print(f"  seed {seed} … ", end="", flush=True)
        metrics = modal_runner.execute(experiment_dir, config, seed)
        if not isinstance(metrics, dict):
            raise TypeError(
                f"Entrypoint must return a dict of metrics, got {type(metrics).__name__}"
            )
        per_seed[seed] = metrics
        print("done", {k: _fmt(v) for k, v in metrics.items()})

    summary = summarize(per_seed)

    # Timestamped artifacts so repeated runs never clobber each other.
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    manifest = build_manifest(config, seeds, cwd=experiment_dir)

    manifest_path = results_dir / f"manifest_{ts}.json"
    results_path = results_dir / f"results_{ts}.json"

    manifest_path.write_text(json.dumps(manifest, indent=2, default=str))
    results_payload = {
        "experiment": experiment_dir.name,
        "config_name": config_name,
        "timestamp_utc": ts,
        "backend": backend,
        "per_seed": {str(s): m for s, m in per_seed.items()},
        "summary": summary,
        "manifest_file": manifest_path.name,
    }
    results_path.write_text(json.dumps(results_payload, indent=2, default=str))

    print()
    print_comparison_table(per_seed, summary)
    print()
    git = manifest["git"]
    dirty = "dirty" if git.get("dirty") else "clean" if git.get("dirty") is not None else "unknown"
    print(f"git: {git.get('commit') or 'n/a'} ({dirty})")
    print(f"manifest -> {manifest_path.relative_to(experiment_dir.parent.parent)}")
    print(f"results  -> {results_path.relative_to(experiment_dir.parent.parent)}")

    return results_payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m shared.runner",
        description="Run a reproducible experiment across seeds.",
    )
    parser.add_argument(
        "--experiment",
        required=True,
        help="Path to the experiment folder (containing config.yaml + intervention.py).",
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Config filename within the experiment folder (default: config.yaml).",
    )
    args = parser.parse_args(argv)

    run_experiment(Path(args.experiment), args.config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
