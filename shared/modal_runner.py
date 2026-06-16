"""Dispatch an experiment entrypoint to either the local machine or a Modal GPU.

The whole point: the experiment code never changes. Flip ``compute.backend`` in the config
between ``local`` (debug on your laptop) and ``modal`` (run scored on a GPU), and the same
``run(config, seed)`` executes in both places.

No secrets live here. The Modal path relies on the credentials you already configured with
``modal token set`` / ``modal setup`` (read from ``~/.modal.toml`` or the standard
``MODAL_TOKEN_ID`` / ``MODAL_TOKEN_SECRET`` env vars by the modal client itself).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any, Callable

try:  # py3.11+ stdlib; fall back to the PyPI backport if needed
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

from shared.seeds import set_all_seeds

# An entrypoint takes the resolved config dict and a seed, and returns a flat metrics dict.
Entrypoint = Callable[[dict, int], dict]


def repo_root() -> Path:
    """The ml-experiments/ directory (parent of shared/)."""
    return Path(__file__).resolve().parent.parent


def read_pinned_deps() -> list[str]:
    """Read the exact dependency pins from pyproject.toml for building the Modal image."""
    pyproject = repo_root() / "pyproject.toml"
    with pyproject.open("rb") as f:
        data = tomllib.load(f)
    return list(data.get("project", {}).get("dependencies", []))


def load_entrypoint(experiment_dir: Path, config: dict | None = None) -> Entrypoint:
    """Load the ``run`` callable from an experiment's entrypoint module.

    Defaults to ``intervention.py``'s ``run`` function; both are overridable via the config
    (``entrypoint`` and ``entry_function``). The experiment dir is put on ``sys.path`` so the
    entrypoint can import sibling modules.
    """
    config = config or {}
    entry_file = config.get("entrypoint", "intervention.py")
    entry_func = config.get("entry_function", "run")

    experiment_dir = Path(experiment_dir).resolve()
    module_path = experiment_dir / entry_file
    if not module_path.exists():
        raise FileNotFoundError(f"Entrypoint not found: {module_path}")

    if str(experiment_dir) not in sys.path:
        sys.path.insert(0, str(experiment_dir))

    mod_name = f"experiment_{experiment_dir.name.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(mod_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load entrypoint from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, entry_func):
        raise AttributeError(
            f"{module_path} does not define '{entry_func}(config, seed)'"
        )
    return getattr(module, entry_func)


def execute(experiment_dir: Path, config: dict, seed: int) -> dict[str, Any]:
    """Run one (experiment, seed) on the backend named in ``config.compute.backend``.

    ``local`` (default) runs in-process; ``modal`` ships it to a Modal GPU. Either way the
    seeds are set immediately before the entrypoint runs.
    """
    backend = config.get("compute", {}).get("backend", "local")
    if backend == "local":
        return _run_local(experiment_dir, config, seed)
    if backend == "modal":
        return _run_modal(experiment_dir, config, seed)
    raise ValueError(
        f"Unknown compute.backend={backend!r} (expected 'local' or 'modal')"
    )


def _run_local(experiment_dir: Path, config: dict, seed: int) -> dict[str, Any]:
    set_all_seeds(seed)
    run = load_entrypoint(experiment_dir, config)
    return run(config, seed)


def _run_modal(experiment_dir: Path, config: dict, seed: int) -> dict[str, Any]:
    import modal  # imported lazily so the local path needs no modal install at import time

    compute = config.get("compute", {})
    gpu = compute.get("gpu", "T4")
    deps = read_pinned_deps()
    root = repo_root()
    exp_rel = Path(experiment_dir).resolve().relative_to(root)

    # Image == the exact pyproject pins, plus the repo source mounted in.
    image = (
        modal.Image.debian_slim(python_version="3.11")
        .pip_install(*deps)
        .add_local_dir(str(root / "shared"), remote_path="/root/shared")
        .add_local_dir(str(root / "experiments"), remote_path="/root/experiments")
    )

    app = modal.App("ml-experiments-runner")

    @app.function(gpu=gpu, image=image, timeout=60 * 60)
    def _remote(config: dict, seed: int, exp_rel: str) -> dict:
        sys.path.insert(0, "/root")
        from pathlib import Path as _Path

        from shared.modal_runner import load_entrypoint as _load
        from shared.seeds import set_all_seeds as _seed

        _seed(seed)
        run = _load(_Path("/root") / exp_rel, config)
        return run(config, seed)

    # Uses your configured modal credentials; nothing secret is read or stored here.
    with app.run():
        return _remote.remote(config, seed, str(exp_rel))
