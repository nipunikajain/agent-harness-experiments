# ml-experiments

A monorepo for running **reproducible** ML/LLM research experiments.

The core idea: an experiment is a folder under `experiments/` with a `config.yaml` and an
`intervention.py` exposing a `run(config, seed) -> dict` entrypoint. A shared runner executes
that entrypoint across multiple seeds, records everything needed to reproduce the run (git
commit + dirty flag, Python version, full `pip freeze`, resolved config), and writes
timestamped JSON results plus a mean±std summary.

The same experiment **debugs locally and runs scored on a Modal GPU** by flipping one field
(`compute.backend`) in `config.yaml`. Nothing about the experiment code changes.

## Layout

```
shared/            # reusable plumbing (runner, modal dispatch, seeding)
experiments/       # one folder per experiment
  example-lr-sweep/
    config.yaml
    intervention.py   # exposes run(config, seed) -> metrics dict
    results/          # timestamped manifests + results land here
    notes.md
```

## Quickstart

```bash
pip install -e .            # or: pip install torch numpy pyyaml modal

# Run the example across its seeds, locally:
python -m shared.runner --experiment experiments/example-lr-sweep

# Controlled comparison — same code, one field changed (the learning rate):
python -m shared.runner --experiment experiments/example-lr-sweep --config config.yaml
python -m shared.runner --experiment experiments/example-lr-sweep --config config.intervention.yaml
```

To run on a GPU instead, set `compute.backend: modal` and `compute.gpu: A10G` (etc.) in the
config. The runner ships the entrypoint to Modal using your existing `modal token` — no
secrets live in this repo.

## Writing a new experiment

1. `cp -r experiments/example-lr-sweep experiments/my-thing`
2. Edit `intervention.py` so `run(config, seed)` does your thing and returns a flat
   `dict[str, float]` of metrics.
3. Edit `config.yaml`. Keep a **baseline** config and an **intervention** config that differ
   in exactly one field, so the comparison is controlled.
4. `python -m shared.runner --experiment experiments/my-thing`

## Results log

| Technique | Date | Result | Verdict | Link |
| --- | --- | --- | --- | --- |
| Long-running-agent harness: structured (1-feature/session, clean state) vs naive, Sonnet 4.6, 10-feature toy | 2026-06-15 | Both 10/10 (identical); structured cost 8.3× tokens / 10× turns for 0 quality gain | Null at tested scale — overhead-only; positive claim untestable on a toy budget | [notes](experiments/2026-06-agent-harness/notes.md) |
| Same harness, stress config: Haiku 4.5, 20 features, tight 80k-token budget | 2026-06-15 | Naive 20/20; structured 7.7/20 (exhausted budget on per-session overhead), 5.9× tokens | Negative — structured strictly dominated; task still one-shot-able so failure mode never engaged | [notes](experiments/2026-06-agent-harness-stress/notes.md) |
