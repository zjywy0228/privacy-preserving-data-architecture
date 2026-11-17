# Differential-Private Training Tools

This folder contains reusable planning, accounting, validation, and mock-safe
training components for differential-private machine learning workflows.

## Components

| File | Purpose |
|---|---|
| `private_training.py` | Opacus private training with a pre-step budget guard |
| `dp_trainer.py` | Training wrapper with per-step privacy-budget accounting and a mock mode for offline validation |
| `budget_accountant.py` | Cumulative privacy-budget accounting and JSON audit logs |
| `privacy_budget_calculator.py` | Pre-run noise multiplier planning and sigma/epsilon sweeps |
| `validate_audit_log.py` | Validation of saved audit logs against the repository schema |
| `visualize_budget.py` | Deterministic SVG chart for a sigma/epsilon sweep |

## Plan a budget

```bash
python dp-llm-training/privacy_budget_calculator.py \
  --dataset-size 50000 \
  --batch-size 64 \
  --epochs 5 \
  --target-epsilon 3 \
  --sweep \
  --output budget-plan.json
```

## Generate a visualization

```bash
python dp-llm-training/visualize_budget.py \
  --dataset-size 50000 \
  --batch-size 64 \
  --epochs 5 \
  --target-epsilon 3 \
  --sigmas 0.5 0.8 1.0 1.5 2.0 3.0 \
  --output docs/figures/dp-budget-sweep.svg
```

The SVG uses a logarithmic epsilon axis and marks the target budget. The
rendering has no plotting-library dependency, so the same sweep rows produce
byte-identical SVG output across supported Python versions.

[View the synthetic-plan example chart.](../docs/figures/dp-budget-sweep.svg)

## Interpretation boundary

The calculator and chart are planning aids. A privacy claim is valid only when
the accountant assumptions match the actual sampling and training loop, and
when all data-dependent runs are included in composition.

## Private training mode

`private_training.py` wraps a compatible model, optimizer, and data loader with
Opacus `make_private`: the `DPOptimizer` clips per-sample gradients at
`max_grad_norm` and adds Gaussian noise scaled by `noise_multiplier`. It uses
Poisson sampling and reads epsilon from the RDP accountant attached to that run.
Before each optimizer step, a copied accountant predicts its cost; the trainer
stops when the next step would exceed `target_epsilon`. Empty Poisson batches
still count as steps. A run stopped before its first step has no epoch log to
export. A budget stop can leave the final epoch partially completed.

Install the optional dependencies and run the synthetic example:

```bash
pip install -e ".[dp]"
python dp-llm-training/examples/private_training_demo.py --seed 0 \
  --audit-log artifacts/private-training-audit.json
python dp-llm-training/validate_audit_log.py artifacts/private-training-audit.json
```

The reference model is a small binary classifier on synthetic data. Its audit
metadata records `training_mode: private`, `accounting_source: opacus-rdp`, and
run provenance. This example uses seeded, non-cryptographic randomness for local
experiments; a production run needs a reviewed secure randomness configuration.
The exported mean training loss is computed directly from the synthetic batches
and has no separate privacy mechanism. For sensitive inputs, restrict these logs
and account separately for any released loss or other data-dependent metrics.
`dp_trainer.py` continues to provide configuration-based planning and accounting.
