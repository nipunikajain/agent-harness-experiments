"""Single source of truth for seeding every RNG an experiment might touch."""

from __future__ import annotations

import os
import random


def set_all_seeds(seed: int) -> None:
    """Seed every RNG we know about so a run is reproducible given the seed.

    Covers Python's ``random``, NumPy, PyTorch (CPU) and PyTorch CUDA. Also sets
    ``PYTHONHASHSEED`` for any hash-randomization-sensitive code. Imports of numpy/torch
    are done lazily so this module is importable in environments that lack them.
    """
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)

    try:
        import numpy as np

        np.random.seed(seed)
    except ImportError:
        pass

    try:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass
