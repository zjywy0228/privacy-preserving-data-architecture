# Differential-Private Training Tools

This folder contains reusable planning, accounting, validation, and mock-safe
training components for differential-private machine learning workflows.

## Components

| File | Purpose |
|---|---|
| `dp_trainer.py` | Differential-private training wrapper with a mock mode for offline validation |
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
