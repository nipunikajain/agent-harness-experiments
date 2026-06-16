"""Example experiment: train a tiny MLP on a trivial, fully-deterministic regression task.

The entrypoint the runner calls is ``run(config, seed) -> metrics dict``. Everything that
affects the result is derived from ``config`` and ``seed``, so the run is reproducible.

The task is a fixed linear teacher (y = X @ w_true + b) with a little noise; the MLP has to
fit it. The only thing the baseline and intervention configs change is ``learning_rate``, so
this is a clean controlled comparison of how the learning rate affects ``final_loss``.
"""

from __future__ import annotations

import torch
import torch.nn as nn


class TinyMLP(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def _make_dataset(n_samples: int, input_dim: int, seed: int):
    """Deterministic given seed: same data for baseline and intervention at a given seed."""
    g = torch.Generator().manual_seed(seed)
    X = torch.randn(n_samples, input_dim, generator=g)
    w_true = torch.randn(input_dim, 1, generator=g)
    b_true = torch.randn(1, generator=g)
    noise = 0.1 * torch.randn(n_samples, 1, generator=g)
    y = X @ w_true + b_true + noise
    return X, y


def run(config: dict, seed: int) -> dict[str, float]:
    model_cfg = config.get("model", {})
    train_cfg = config.get("training", {})

    input_dim = int(model_cfg.get("input_dim", 16))
    hidden_dim = int(model_cfg.get("hidden_dim", 32))
    n_samples = int(train_cfg.get("n_samples", 512))
    epochs = int(train_cfg.get("epochs", 100))
    batch_size = int(train_cfg.get("batch_size", 64))
    learning_rate = float(config["learning_rate"])  # the single variable under study

    # set_all_seeds(seed) has already been called by the runner/dispatch layer; we additionally
    # seed the dataset generator explicitly so data is identical across configs at a given seed.
    X, y = _make_dataset(n_samples, input_dim, seed)

    model = TinyMLP(input_dim, hidden_dim)
    optimizer = torch.optim.SGD(model.parameters(), lr=learning_rate)
    loss_fn = nn.MSELoss()

    with torch.no_grad():
        initial_loss = loss_fn(model(X), y).item()

    n_batches = max(1, n_samples // batch_size)
    final_epoch_loss = float("nan")
    for _epoch in range(epochs):
        perm = torch.randperm(n_samples)
        epoch_loss = 0.0
        for b in range(n_batches):
            idx = perm[b * batch_size : (b + 1) * batch_size]
            xb, yb = X[idx], y[idx]
            optimizer.zero_grad()
            loss = loss_fn(model(xb), yb)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
        final_epoch_loss = epoch_loss / n_batches

    with torch.no_grad():
        final_loss = loss_fn(model(X), y).item()

    return {
        "final_loss": final_loss,
        "final_epoch_loss": final_epoch_loss,
        "initial_loss": initial_loss,
        "learning_rate": learning_rate,
    }
