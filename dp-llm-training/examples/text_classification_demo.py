"""
Text Classification Demo: Differentially Private Training with Budget Audit Log

This demo simulates three epochs of DP text classification training.
No real model or data is required -- DPTrainer and BudgetAccountant both
support a mock mode (model=None, optimizer=None) for architecture review
and CI/CD pipelines without GPU/torch dependencies.

Demonstrates:
    - Configuring DPTrainer with realistic dataset parameters
    - Running simulated batch steps per epoch
    - Recording per-epoch privacy costs with BudgetAccountant
    - Printing a formatted per-epoch table
    - Saving and displaying the JSON audit log
"""

import json
import sys
import os

# ---------------------------------------------------------------------------
# Path setup: make dp-llm-training directory importable from any working dir
# ---------------------------------------------------------------------------
_DP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _DP_DIR not in sys.path:
    sys.path.insert(0, _DP_DIR)

from dp_trainer import DPTrainer, PrivacyConfig           # noqa: E402
from budget_accountant import BudgetAccountant            # noqa: E402

# ---------------------------------------------------------------------------
# Simulation parameters (realistic text classification workload)
# ---------------------------------------------------------------------------
DATASET_SIZE = 5_000
BATCH_SIZE = 64
NUM_EPOCHS = 3
TARGET_EPSILON = 3.0
TARGET_DELTA = 1.0 / DATASET_SIZE   # 2e-4, standard choice of 1/N
NOISE_MULTIPLIER = 1.1
MAX_GRAD_NORM = 1.0

SAMPLE_RATE = BATCH_SIZE / DATASET_SIZE
STEPS_PER_EPOCH = DATASET_SIZE // BATCH_SIZE   # 78 steps per epoch


def simulate_epoch_loss(epoch: int) -> float:
    """Return a plausible decreasing mock loss for the given epoch number."""
    base_losses = {1: 2.312, 2: 1.874, 3: 1.531}
    return base_losses.get(epoch, 1.2)


def print_table_header() -> None:
    print("\n" + "=" * 75)
    print(f"  {'Epoch':>5}  {'Steps':>6}  {'Loss':>7}  {'Epsilon':>9}  "
          f"{'Budget%':>8}  {'Remaining':>10}  {'Exhausted':>9}")
    print("-" * 75)


def print_table_row(entry: dict, remaining: float) -> None:
    print(
        f"  {entry['epoch']:>5}  "
        f"{entry['cumulative_steps']:>6}  "
        f"{entry['loss']:>7.4f}  "
        f"{entry['epsilon_spent']:>9.5f}  "
        f"{entry['budget_fraction'] * 100:>7.2f}%  "
        f"{remaining:>10.5f}  "
        f"{'YES' if entry['budget_exhausted'] else 'no':>9}"
    )


def run_demo(audit_log_path: str = "dp_audit_log.json") -> None:
    """Run the full simulated training demo."""

    config = PrivacyConfig(
        target_epsilon=TARGET_EPSILON,
        target_delta=TARGET_DELTA,
        max_grad_norm=MAX_GRAD_NORM,
        noise_multiplier=NOISE_MULTIPLIER,
    )

    trainer = DPTrainer(
        model=None,
        optimizer=None,
        config=config,
        dataset_size=DATASET_SIZE,
        batch_size=BATCH_SIZE,
    )

    accountant = BudgetAccountant(
        target_epsilon=TARGET_EPSILON,
        target_delta=TARGET_DELTA,
        noise_multiplier=NOISE_MULTIPLIER,
        sample_rate=SAMPLE_RATE,
    )

    print("\nDP Text Classification Training Demo")
    print(f"  Dataset size : {DATASET_SIZE:,} samples")
    print(f"  Batch size   : {BATCH_SIZE}")
    print(f"  Steps/epoch  : {STEPS_PER_EPOCH}")
    print(f"  Target eps   : {TARGET_EPSILON}  (delta={TARGET_DELTA:.2e})")
    print(f"  Noise mult.  : {NOISE_MULTIPLIER}")
    print(config.describe())

    print_table_header()

    for epoch in range(1, NUM_EPOCHS + 1):
        for _ in range(STEPS_PER_EPOCH):
            trainer.step({"input": None, "label": None})

        avg_loss = simulate_epoch_loss(epoch)

        entry = accountant.record_epoch(
            epoch=epoch,
            steps_in_epoch=STEPS_PER_EPOCH,
            loss=avg_loss,
        )

        print_table_row(entry, accountant.remaining_budget())

        if trainer.should_stop():
            print(f"\n  [STOP] DPTrainer: epsilon budget exhausted at epoch {epoch}.")
            break

    print("=" * 75)

    # ------------------------------------------------------------------
    # Final summary
    # ------------------------------------------------------------------
    summary = accountant.summary()
    print("\nFinal Privacy Accounting Summary:")
    for key, val in summary.items():
        print(f"  {key:<22}: {val}")

    # ------------------------------------------------------------------
    # Save and display audit log
    # ------------------------------------------------------------------
    accountant.save_log(audit_log_path)
    print(f"\nAudit log saved to: {audit_log_path}")

    loaded = BudgetAccountant.load_log(audit_log_path)
    print("\nAudit log snippet (first entry):")
    print(json.dumps(loaded[0], indent=2))

    print(f"\nFinal epsilon: {summary['epsilon_spent']:.5f} / {TARGET_EPSILON}  "
          f"({summary['remaining_budget']:.5f} remaining)")


if __name__ == "__main__":
    run_demo()
