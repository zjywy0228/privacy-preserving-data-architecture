"""
DP Training Validation Runner

Sweeps the noise multiplier σ over a configurable range and measures how
the privacy budget (ε, δ) changes across training epochs.  Reports an
epsilon-vs-steps table suitable for privacy-accuracy tradeoff analysis.

No real model, GPU, or Opacus installation is required.  DPTrainer runs in
mock mode (model=None) while the privacy accounting is fully live.

Usage
-----
    # Default sweep (σ = 0.6, 1.0, 1.1, 1.5; 3 epochs, AG-News-scale):
    python validation/run_dp_validation.py

    # Custom parameters, save JSON:
    python validation/run_dp_validation.py \\
        --dataset-size 50000 --batch-size 256 --epochs 5 \\
        --sigmas 0.5 1.0 2.0 --output validation/dp_validation_report.json

Output
------
Per-epoch rows for each σ value:
  sigma | epoch | steps | epsilon | budget_pct | exhausted
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent
_DP_DIR = _REPO_ROOT / "dp-llm-training"
if str(_DP_DIR) not in sys.path:
    sys.path.insert(0, str(_DP_DIR))

from dp_trainer import DPTrainer, PrivacyConfig  # noqa: E402


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class EpochRecord:
    sigma: float
    epoch: int
    cumulative_steps: int
    epsilon: float
    budget_pct: float
    exhausted: bool


# ---------------------------------------------------------------------------
# Core validation
# ---------------------------------------------------------------------------


def run_sigma(
    sigma: float,
    dataset_size: int,
    batch_size: int,
    num_epochs: int,
    target_epsilon: float,
    target_delta: float,
) -> list[EpochRecord]:
    """
    Simulate training for `num_epochs` with the given σ and record
    privacy budget consumption per epoch.
    """
    config = PrivacyConfig(
        target_epsilon=target_epsilon,
        target_delta=target_delta,
        noise_multiplier=sigma,
        max_grad_norm=1.0,
    )
    trainer = DPTrainer(
        model=None,
        optimizer=None,
        config=config,
        dataset_size=dataset_size,
        batch_size=batch_size,
    )

    steps_per_epoch = max(1, dataset_size // batch_size)
    records: list[EpochRecord] = []

    for epoch in range(1, num_epochs + 1):
        for _ in range(steps_per_epoch):
            trainer.step(batch=None)
            if trainer.should_stop():
                break

        summary = trainer.privacy_budget_spent()
        eps = summary["epsilon_spent"]
        budget_pct = min(100.0, round(eps / target_epsilon * 100, 2))

        records.append(
            EpochRecord(
                sigma=sigma,
                epoch=epoch,
                cumulative_steps=summary["steps_trained"],
                epsilon=round(eps, 6),
                budget_pct=budget_pct,
                exhausted=summary["budget_exhausted"],
            )
        )

        if trainer.should_stop():
            # Fill remaining epochs with a sentinel to show budget was exhausted
            for rem_epoch in range(epoch + 1, num_epochs + 1):
                records.append(
                    EpochRecord(
                        sigma=sigma,
                        epoch=rem_epoch,
                        cumulative_steps=summary["steps_trained"],
                        epsilon=round(eps, 6),
                        budget_pct=100.0,
                        exhausted=True,
                    )
                )
            break

    return records


def run_sweep(
    sigmas: list[float],
    dataset_size: int,
    batch_size: int,
    num_epochs: int,
    target_epsilon: float,
    target_delta: float,
) -> list[EpochRecord]:
    all_records: list[EpochRecord] = []
    for sigma in sigmas:
        all_records.extend(
            run_sigma(sigma, dataset_size, batch_size, num_epochs, target_epsilon, target_delta)
        )
    return all_records


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def _print_table(records: list[EpochRecord], target_epsilon: float) -> None:
    last_sigma: float | None = None
    header = (
        f"  {'σ':>6}  {'epoch':>5}  {'steps':>7}  "
        f"{'epsilon':>9}  {'budget%':>8}  {'exhausted':>9}"
    )
    sep = "  " + "─" * (len(header) - 2)

    print(f"\n  DP Training Validation (target ε = {target_epsilon})")
    print(sep)
    print(header)
    print(sep)

    for r in records:
        if last_sigma is not None and r.sigma != last_sigma:
            print()
        last_sigma = r.sigma
        exh_str = "YES" if r.exhausted else "no"
        print(
            f"  {r.sigma:>6.2f}  {r.epoch:>5}  {r.cumulative_steps:>7}  "
            f"{r.epsilon:>9.5f}  {r.budget_pct:>7.2f}%  {exh_str:>9}"
        )

    print(sep)
    print()


def _summarise(records: list[EpochRecord]) -> dict[str, Any]:
    """Compute per-sigma final-epoch summary for JSON output."""
    sigmas = sorted({r.sigma for r in records})
    summary: dict[str, Any] = {}
    for sigma in sigmas:
        rows = [r for r in records if r.sigma == sigma]
        last = rows[-1]
        summary[str(sigma)] = {
            "sigma": sigma,
            "final_epsilon": last.epsilon,
            "final_budget_pct": last.budget_pct,
            "budget_exhausted": last.exhausted,
            "epochs_completed": last.epoch if not last.exhausted else
                next((r.epoch for r in rows if r.exhausted), last.epoch),
        }
    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="run_dp_validation",
        description="Sweep noise multiplier σ and show per-epoch privacy budget.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--dataset-size",    type=int,   default=120_000)
    p.add_argument("--batch-size",      type=int,   default=256)
    p.add_argument("--epochs",          type=int,   default=3)
    p.add_argument("--target-epsilon",  type=float, default=3.0)
    p.add_argument("--target-delta",    type=float, default=None)
    p.add_argument(
        "--sigmas",
        type=float,
        nargs="+",
        default=[0.6, 1.0, 1.1, 1.5],
        metavar="SIGMA",
    )
    p.add_argument("--output", type=str, default=None, metavar="FILE")
    return p


def main(argv: list[str] | None = None) -> None:
    args = _build_parser().parse_args(argv)
    delta = args.target_delta if args.target_delta is not None else 1.0 / args.dataset_size

    records = run_sweep(
        sigmas=args.sigmas,
        dataset_size=args.dataset_size,
        batch_size=args.batch_size,
        num_epochs=args.epochs,
        target_epsilon=args.target_epsilon,
        target_delta=delta,
    )

    _print_table(records, args.target_epsilon)

    if args.output:
        out = {
            "schema_version": "1.0",
            "params": {
                "dataset_size": args.dataset_size,
                "batch_size": args.batch_size,
                "epochs": args.epochs,
                "target_epsilon": args.target_epsilon,
                "target_delta": delta,
                "sigmas": args.sigmas,
            },
            "per_sigma_summary": _summarise(records),
            "epoch_records": [
                {
                    "sigma": r.sigma,
                    "epoch": r.epoch,
                    "cumulative_steps": r.cumulative_steps,
                    "epsilon": r.epsilon,
                    "budget_pct": r.budget_pct,
                    "exhausted": r.exhausted,
                }
                for r in records
            ],
        }
        with open(args.output, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2)
        print(f"  [✓] Report written to {args.output}")


if __name__ == "__main__":
    main()
