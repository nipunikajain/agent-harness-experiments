"""Driver for the DB-harness sweep: model × strategy × seed, with a hard USD kill-switch.

Reuses the shared agent loop (shared/agent.py), the DB grader (shared/agent_eval_db.py), and
the provenance/manifest helpers (shared/runner.py). Writes one JSON per run under
results/runs/ (resumable: existing runs are skipped), aggregates into a comparison table, and
writes a timestamped combined results file + manifest.

Usage:
    python -m experiments.2026-06-db-harness.run_sweep        # not importable (dashes); use:
    python experiments/2026-06-db-harness/run_sweep.py [--config config.yaml]

Credentials: ANTHROPIC_API_KEY via environment or the repo-root .env (auto-loaded).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

EXPERIMENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = EXPERIMENT_DIR.parents[1]
sys.path.insert(0, str(REPO_ROOT))

from shared import agent, agent_eval_db, runner  # noqa: E402


def _load_dotenv() -> None:
    for root in (REPO_ROOT, EXPERIMENT_DIR):
        env_file = root / ".env"
        if not env_file.exists():
            continue
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                k, v = k.strip(), v.strip().strip('"').strip("'")
                if k.startswith("ANTHROPIC_") and k not in os.environ:
                    os.environ[k] = v


def _features(cfg) -> list[dict]:
    data = yaml.safe_load((EXPERIMENT_DIR / cfg["task"]["features_file"]).read_text())
    feats = data["features"][: cfg["task"]["n_features"]]
    return [{"id": f["id"], "name": f["name"], "spec": " ".join(f["spec"].split())} for f in feats]


def _one_run(client, model, strategy, seed, features, cfg, preamble, results_dir):
    n = cfg["task"]["n_features"]
    ws = results_dir / "_workspaces" / model / strategy / f"seed_{seed}"
    if ws.exists():
        shutil.rmtree(ws)
    ws.mkdir(parents=True, exist_ok=True)

    run_cfg = {
        "model": model,
        "temperature": float(cfg.get("temperature", 1.0)),
        "max_output_tokens": int(cfg.get("max_output_tokens", 4096)),
        "max_turns": int(cfg.get("max_turns", 40)),
        "max_turns_per_feature": int(cfg.get("max_turns_per_feature", 6)),
        "task_preamble": preamble,
    }
    budget = agent.RunBudget(int(cfg["budget"]["max_total_tokens"]), model)

    info = agent.STRATEGIES[strategy](client, ws, features, run_cfg, budget, agent_eval_db)
    grade = agent_eval_db.run_checks(ws, n)
    final = grade["passed"]
    peak = max(info.get("peak_passed", final), final)
    return {
        "model": model, "strategy": strategy, "seed": seed,
        "features_passed": final, "features_total": grade["total"],
        "peak_passed": peak, "regressions": peak - final,
        "sessions": info["sessions"], "turns": info["turns"],
        "tokens_in": budget.input_tokens, "tokens_out": budget.output_tokens,
        "total_tokens": budget.total_tokens, "est_cost_usd": round(budget.est_cost_usd, 4),
        "budget_hit_tokens": budget.exhausted(), "killed_on_usd": info["turns"] == -1,
    }


def _agg(rows):
    def ms(vals):
        return {"mean": statistics.mean(vals),
                "std": statistics.pstdev(vals) if len(vals) > 1 else 0.0, "n": len(vals)}
    return {
        "features_passed": ms([r["features_passed"] for r in rows]),
        "peak_passed": ms([r["peak_passed"] for r in rows]),
        "regressions": ms([r["regressions"] for r in rows]),
        "total_tokens": ms([r["total_tokens"] for r in rows]),
        "est_cost_usd": ms([r["est_cost_usd"] for r in rows]),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    args = ap.parse_args()

    cfg = yaml.safe_load((EXPERIMENT_DIR / args.config).read_text())
    _load_dotenv()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY not set (put it in ml-experiments/.env).")

    import anthropic
    client = anthropic.Anthropic()

    results_dir = EXPERIMENT_DIR / "results"
    runs_dir = results_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    preamble = (EXPERIMENT_DIR / cfg["task"]["contract_file"]).read_text()

    ledger = results_dir / ".spend_ledger.json"
    acc = agent.Accountant(ledger, float(cfg["budget"]["usd_cap"]))
    agent.set_accountant(acc)
    features = _features(cfg)

    # Build the run list (model, strategy, seed).
    plan = []
    for m in cfg["sweep"]["models"]:
        for strat in cfg["sweep"]["strategies"]:
            for seed in m["seeds"]:
                plan.append((m["id"], strat, seed))

    print(f"Sweep: {len(plan)} runs | usd_cap=${acc.usd_cap:.2f} | already spent ${acc.spent():.4f}\n")
    for (model, strat, seed) in plan:
        run_file = runs_dir / f"{model}__{strat}__seed{seed}.json"
        if run_file.exists():
            print(f"  skip (done): {model} {strat} seed{seed}")
            continue
        if acc.remaining() < 0.50:
            print(f"  STOP: only ${acc.remaining():.2f} left under cap — not starting new runs.")
            break
        short = model.split("-")[1]
        print(f"  run: {short:7} {strat:11} seed{seed} … ", end="", flush=True)
        try:
            row = _one_run(client, model, strat, seed, features, cfg, preamble, results_dir)
            run_file.write_text(json.dumps(row, indent=2))
            tag = " [KILLED on USD cap]" if row["killed_on_usd"] else ""
            print(f"passed {row['features_passed']}/{row['features_total']} "
                  f"(peak {row['peak_passed']}, regr {row['regressions']}) "
                  f"${row['est_cost_usd']:.3f} | ledger ${acc.spent():.3f}{tag}")
        except agent.BudgetExceeded as e:
            print(f"BUDGET KILL: {e}")
            break

    # Aggregate everything on disk.
    all_rows = [json.loads(p.read_text()) for p in sorted(runs_dir.glob("*.json"))]
    if not all_rows:
        print("\nNo runs recorded.")
        return

    print("\n===== RESULTS =====")
    by_model: dict[str, dict[str, list]] = {}
    for r in all_rows:
        by_model.setdefault(r["model"], {}).setdefault(r["strategy"], []).append(r)

    summary = {}
    for model, arms in by_model.items():
        print(f"\n## {model}")
        print(f"{'metric':16} {'naive (mean±std)':24} {'structured (mean±std)':24} delta")
        a_naive = _agg(arms.get("naive", [])) if arms.get("naive") else None
        a_struct = _agg(arms.get("structured", [])) if arms.get("structured") else None
        summary[model] = {"naive": a_naive, "structured": a_struct,
                          "n_naive": len(arms.get("naive", [])), "n_structured": len(arms.get("structured", []))}
        for metric in ["features_passed", "peak_passed", "regressions", "total_tokens", "est_cost_usd"]:
            nv = a_naive[metric] if a_naive else None
            sv = a_struct[metric] if a_struct else None
            if nv and sv:
                delta = sv["mean"] - nv["mean"]
                print(f"{metric:16} {nv['mean']:.3g} ± {nv['std']:.3g}".ljust(41) +
                      f"{sv['mean']:.3g} ± {sv['std']:.3g}".ljust(24) + f"{delta:+.3g}")

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    manifest = runner.build_manifest(cfg, [r["seed"] for r in all_rows], cwd=EXPERIMENT_DIR)
    (results_dir / f"manifest_{ts}.json").write_text(json.dumps(manifest, indent=2, default=str))
    (results_dir / f"results_{ts}.json").write_text(json.dumps(
        {"runs": all_rows, "summary": summary, "total_spent_usd": acc.spent()}, indent=2, default=str))
    print(f"\ntotal spent this sweep ledger: ${acc.spent():.3f}")
    print(f"results -> results/results_{ts}.json")


if __name__ == "__main__":
    main()
