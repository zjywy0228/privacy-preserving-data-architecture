"""
DP Privacy Budget Calculator — CLI Tool

Answers two questions a practitioner faces before starting a DP training run:

  1. Given my dataset and training plan, what noise multiplier σ do I need
     to stay within a target (ε, δ) privacy budget?

  2. How does my privacy budget trade off against noise intensity?  (sensitivity
     table: ε as a function of σ at fixed dataset/batch/epoch parameters)

Uses the same self-contained RDP accountant as budget_accountant.py so the
tool can be run without installing Opacus or PyTorch.

Typical usage
-------------
  # Required noise for AG News–scale fine-tuning:
  python privacy_budget_calculator.py \\
      --dataset-size 120000 --batch-size 128 --epochs 3 --target-epsilon 3.0

  # Sweep σ from 0.5 to 2.0, show resulting ε, export JSON:
  python privacy_budget_calculator.py \\
      --dataset-size 50000 --batch-size 64 --epochs 5 \\
      --target-epsilon 8.0 --sweep --output budget_plan.json

References
----------
  Mironov, I. (2017). Rényi Differential Privacy of the Gaussian Mechanism.
  IEEE CSF. doi:10.1109/CSF.2017.11

  Abadi et al. (2016). Deep Learning with Differential Privacy.
  ACM CCS. doi:10.1145/2976749.2978318

  Zhang et al. (2025). A Differential Privacy-Based Mechanism for Preventing
  Data Leakage in LLM Training. Neural Processing Letters.
  doi:10.1007/s11063-024-11604-9
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from typing import Any

# ---------------------------------------------------------------------------
# RDP epsilon computation (self-contained, no Opacus required)
# ---------------------------------------------------------------------------


def _rdp_epsilon(
    noise_multiplier: float,
    sample_rate: float,
    steps: int,
    delta: float,
    orders: list[int] | None = None,
) -> float:
    """
    Estimate (ε, δ)-DP epsilon via the Mironov 2017 RDP composition bound.

    Args:
        noise_multiplier: σ / clip_norm ratio.
        sample_rate:      batch_size / dataset_size.
        steps:            total gradient update steps.
        delta:            target delta.
        orders:           RDP orders to evaluate (wider range → tighter bound).

    Returns:
        Estimated ε under (ε, δ)-DP.
    """
    if orders is None:
        orders = list(range(2, 128)) + [256, 512, 1024]

    # Try Opacus for a tighter bound if available
    try:
        from opacus.accountants import RDPAccountant  # type: ignore[import]

        acc = RDPAccountant()
        acc.history = [(noise_multiplier, sample_rate, steps)]
        eps, _ = acc.get_privacy_spent(delta=delta, alphas=orders)
        return float(eps)
    except Exception:
        pass

    # Analytical fallback (Mironov 2017 Theorem 3)
    best = math.inf
    for alpha in orders:
        if alpha <= 1:
            continue
        log_moment = steps * (sample_rate**2) * alpha / (2.0 * noise_multiplier**2)
        candidate = log_moment + math.log(1.0 / delta) / (alpha - 1)
        best = min(best, candidate)
    return best


def _find_noise_multiplier(
    target_epsilon: float,
    sample_rate: float,
    steps: int,
    delta: float,
    tol: float = 1e-4,
) -> float:
    """
    Binary search for the minimum σ that satisfies ε ≤ target_epsilon.

    Returns the noise multiplier (rounded up to 4 decimal places).
    """
    lo, hi = 0.05, 1000.0

    # Sanity check: ensure hi gives ε ≤ target_epsilon
    if _rdp_epsilon(hi, sample_rate, steps, delta) > target_epsilon:
        return math.inf  # infeasible

    for _ in range(100):
        mid = (lo + hi) / 2.0
        eps = _rdp_epsilon(mid, sample_rate, steps, delta)
        if eps > target_epsilon:
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break

    # Round up to ensure we stay within budget
    return round(hi + tol, 4)


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------


@dataclass
class BudgetPlan:
    dataset_size: int
    batch_size: int
    epochs: int
    steps: int
    sample_rate: float
    target_epsilon: float
    target_delta: float
    required_noise_multiplier: float
    epsilon_at_required_sigma: float
    feasible: bool


@dataclass
class SweepRow:
    noise_multiplier: float
    epsilon: float
    within_budget: bool


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------


def compute_plan(
    dataset_size: int,
    batch_size: int,
    epochs: int,
    target_epsilon: float,
    target_delta: float,
) -> BudgetPlan:
    """Compute the noise multiplier needed to meet the budget."""
    sample_rate = batch_size / dataset_size
    steps = int(epochs * dataset_size / batch_size)

    sigma = _find_noise_multiplier(target_epsilon, sample_rate, steps, target_delta)
    feasible = sigma < 1000.0

    eps_actual = _rdp_epsilon(sigma, sample_rate, steps, target_delta) if feasible else math.inf

    return BudgetPlan(
        dataset_size=dataset_size,
        batch_size=batch_size,
        epochs=epochs,
        steps=steps,
        sample_rate=round(sample_rate, 6),
        target_epsilon=target_epsilon,
        target_delta=target_delta,
        required_noise_multiplier=sigma if feasible else math.inf,
        epsilon_at_required_sigma=round(eps_actual, 6),
        feasible=feasible,
    )


def sweep_sigma(
    dataset_size: int,
    batch_size: int,
    epochs: int,
    target_epsilon: float,
    target_delta: float,
    sigma_values: list[float] | None = None,
) -> list[SweepRow]:
    """
    Evaluate ε at a range of σ values (sensitivity table).

    Default σ sweep: 0.4, 0.5, 0.6, 0.8, 1.0, 1.1, 1.2, 1.5, 2.0, 3.0
    """
    if sigma_values is None:
        sigma_values = [0.4, 0.5, 0.6, 0.8, 1.0, 1.1, 1.2, 1.5, 2.0, 3.0]

    sample_rate = batch_size / dataset_size
    steps = int(epochs * dataset_size / batch_size)

    rows: list[SweepRow] = []
    for sigma in sorted(sigma_values):
        eps = _rdp_epsilon(sigma, sample_rate, steps, target_delta)
        rows.append(
            SweepRow(
                noise_multiplier=sigma,
                epsilon=round(eps, 4),
                within_budget=eps <= target_epsilon,
            )
        )
    return rows


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _fmt_plan(plan: BudgetPlan) -> str:
    lines = [
        "",
        "  DP Training Budget Plan",
        "  " + "─" * 40,
        f"  Dataset size      : {plan.dataset_size:,}",
        f"  Batch size        : {plan.batch_size}",
        f"  Epochs            : {plan.epochs}",
        f"  Total steps       : {plan.steps:,}",
        f"  Sample rate       : {plan.sample_rate:.6f}",
        f"  Target ε          : {plan.target_epsilon}",
        f"  Target δ          : {plan.target_delta:.2e}",
        "  " + "─" * 40,
    ]
    if plan.feasible:
        lines += [
            f"  Required σ        : {plan.required_noise_multiplier}",
            f"  Actual ε at σ     : {plan.epsilon_at_required_sigma:.6f}",
            "  Status            : FEASIBLE ✓",
        ]
    else:
        lines += [
            "  Required σ        : INFEASIBLE",
            "  Status            : No σ achieves this ε budget",
        ]
    lines.append("")
    return "\n".join(lines)


def _fmt_sweep(rows: list[SweepRow], target_epsilon: float) -> str:
    lines = [
        "",
        "  σ Sensitivity Table",
        f"  (target ε = {target_epsilon})",
        "",
        f"  {'σ (noise_mult)':>15}  {'ε (epsilon)':>12}  {'Within budget':>13}",
        "  " + "─" * 45,
    ]
    for r in rows:
        budget_str = "✓ yes" if r.within_budget else "✗ no"
        lines.append(f"  {r.noise_multiplier:>15.2f}  {r.epsilon:>12.4f}  {budget_str:>13}")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="privacy_budget_calculator",
        description=(
            "Compute the noise multiplier needed for a target (ε, δ)-DP budget, "
            "and optionally sweep σ to show the ε tradeoff."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "--dataset-size",
        type=int,
        required=True,
        help="Number of training examples.",
    )
    p.add_argument(
        "--batch-size",
        type=int,
        required=True,
        help="Mini-batch size per gradient step.",
    )
    p.add_argument(
        "--epochs",
        type=int,
        required=True,
        help="Number of training epochs.",
    )
    p.add_argument(
        "--target-epsilon",
        type=float,
        default=3.0,
        help="Maximum allowed ε. Common values: 1 (strong), 3 (moderate), 8 (weak).",
    )
    p.add_argument(
        "--target-delta",
        type=float,
        default=None,
        help=(
            "Target δ. Defaults to 1/dataset_size (standard choice). "
            "Must be << 1 and typically ≤ 1e-5."
        ),
    )
    p.add_argument(
        "--sweep",
        action="store_true",
        help="Print a sensitivity table of ε vs σ.",
    )
    p.add_argument(
        "--sweep-sigmas",
        type=float,
        nargs="+",
        default=None,
        metavar="SIGMA",
        help="Custom σ values for the sweep (e.g. --sweep-sigmas 0.5 1.0 1.5 2.0).",
    )
    p.add_argument(
        "--output",
        type=str,
        default=None,
        metavar="FILE",
        help="Write JSON report to FILE (optional).",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    delta = args.target_delta if args.target_delta is not None else 1.0 / args.dataset_size

    plan = compute_plan(
        dataset_size=args.dataset_size,
        batch_size=args.batch_size,
        epochs=args.epochs,
        target_epsilon=args.target_epsilon,
        target_delta=delta,
    )

    print(_fmt_plan(plan))

    sweep_rows: list[SweepRow] = []
    if args.sweep or args.sweep_sigmas:
        sweep_rows = sweep_sigma(
            dataset_size=args.dataset_size,
            batch_size=args.batch_size,
            epochs=args.epochs,
            target_epsilon=args.target_epsilon,
            target_delta=delta,
            sigma_values=args.sweep_sigmas,
        )
        print(_fmt_sweep(sweep_rows, args.target_epsilon))

    if args.output:
        report: dict[str, Any] = {
            "plan": asdict(plan),
            "sweep": [asdict(r) for r in sweep_rows],
        }
        with open(args.output, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
        print(f"  [✓] JSON report written to {args.output}")


if __name__ == "__main__":
    main()
