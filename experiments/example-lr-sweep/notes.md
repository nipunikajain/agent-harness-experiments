# example-lr-sweep

## Question
Does this monorepo's controlled-comparison plumbing actually work end-to-end? Train a tiny
MLP on a fixed linear-regression task and check that changing **only** the learning rate
moves `final_loss` in a predictable way.

## Setup
- Model: `TinyMLP` (Linear → ReLU → Linear), `input_dim=16`, `hidden_dim=32`.
- Data: fixed linear teacher `y = X @ w_true + b_true + noise`, deterministic per seed.
- Optimizer: plain SGD. Loss: MSE. 100 epochs, batch size 64, 512 samples.
- Seeds: `[0, 1, 2]` → results reported as mean ± std.

## The controlled variable
`learning_rate`, and nothing else.
- `config.yaml` — baseline, `lr = 0.01`
- `config.intervention.yaml` — intervention, `lr = 0.1`

Both configs are byte-for-byte identical apart from that one field, and the dataset for a
given seed is identical across configs. So any difference in `final_loss` is attributable to
the learning rate.

## How to run
```bash
python -m shared.runner --experiment experiments/example-lr-sweep --config config.yaml
python -m shared.runner --experiment experiments/example-lr-sweep --config config.intervention.yaml
```

## Expected
With plain SGD on this easy task, `lr=0.1` should converge much faster than `lr=0.01` within
100 epochs, so the intervention's `final_loss` should be substantially lower. (Crank it too
high — e.g. `lr=1.0` — and you'd see divergence instead; a useful third config to try.)

## Observations
_(fill in after running — copy the mean ± std from the runner's table, and log the verdict in
the top-level README results table.)_
