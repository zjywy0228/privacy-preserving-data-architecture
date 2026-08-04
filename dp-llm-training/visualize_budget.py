"""Render a deterministic SVG privacy-budget sensitivity chart."""

from __future__ import annotations

import argparse
import html
import math
from pathlib import Path
from typing import Any

from privacy_budget_calculator import SweepRow, sweep_sigma


def compute_sweep(
    dataset_size: int,
    batch_size: int,
    epochs: int,
    target_epsilon: float,
    target_delta: float,
    sigma_values: list[float] | None = None,
) -> list[SweepRow]:
    """Validate parameters and compute epsilon values across noise multipliers."""
    if dataset_size <= 0:
        raise ValueError("dataset_size must be positive.")
    if batch_size <= 0 or batch_size > dataset_size:
        raise ValueError("batch_size must be positive and no larger than dataset_size.")
    if epochs <= 0:
        raise ValueError("epochs must be positive.")
    if target_epsilon <= 0 or not math.isfinite(target_epsilon):
        raise ValueError("target_epsilon must be finite and positive.")
    if not 0 < target_delta < 1:
        raise ValueError("target_delta must be between zero and one.")
    if sigma_values is not None and (
        not sigma_values or any(sigma <= 0 or not math.isfinite(sigma) for sigma in sigma_values)
    ):
        raise ValueError("sigma values must be finite and positive.")

    return sweep_sigma(
        dataset_size=dataset_size,
        batch_size=batch_size,
        epochs=epochs,
        target_epsilon=target_epsilon,
        target_delta=target_delta,
        sigma_values=sigma_values,
    )


def _point(value: float) -> str:
    return f"{value:.2f}"


def render_svg(
    rows: list[SweepRow],
    target_epsilon: float,
    title: str = "Differential-Privacy Budget Sensitivity",
    metadata: dict[str, Any] | None = None,
) -> str:
    """Render rows as a standalone SVG with a logarithmic epsilon axis."""
    if not rows:
        raise ValueError("At least one sweep row is required.")
    if target_epsilon <= 0 or not math.isfinite(target_epsilon):
        raise ValueError("target_epsilon must be finite and positive.")
    if any(
        row.noise_multiplier <= 0
        or row.epsilon <= 0
        or not math.isfinite(row.noise_multiplier)
        or not math.isfinite(row.epsilon)
        for row in rows
    ):
        raise ValueError("Sweep rows must contain finite, positive values.")

    ordered = sorted(rows, key=lambda row: row.noise_multiplier)
    width, height = 900, 540
    left, right, top, bottom = 85, 35, 75, 85
    plot_width = width - left - right
    plot_height = height - top - bottom

    x_min = ordered[0].noise_multiplier
    x_max = ordered[-1].noise_multiplier
    log_values = [math.log10(row.epsilon) for row in ordered]
    target_log = math.log10(target_epsilon)
    y_min = min(log_values + [target_log])
    y_max = max(log_values + [target_log])
    if math.isclose(y_min, y_max):
        y_min -= 0.5
        y_max += 0.5
    else:
        padding = (y_max - y_min) * 0.08
        y_min -= padding
        y_max += padding

    def x_position(sigma: float) -> float:
        if math.isclose(x_min, x_max):
            return left + plot_width / 2
        return left + (sigma - x_min) / (x_max - x_min) * plot_width

    def y_position(epsilon: float) -> float:
        return top + (y_max - math.log10(epsilon)) / (y_max - y_min) * plot_height

    points = " ".join(
        f"{_point(x_position(row.noise_multiplier))},{_point(y_position(row.epsilon))}"
        for row in ordered
    )
    circles = "\n".join(
        (
            f'    <circle cx="{_point(x_position(row.noise_multiplier))}" '
            f'cy="{_point(y_position(row.epsilon))}" r="5" '
            f'class="{"within" if row.within_budget else "over"}">'
            f"<title>sigma={row.noise_multiplier:g}, epsilon={row.epsilon:g}, "
            f"{'within' if row.within_budget else 'over'} budget</title></circle>"
        )
        for row in ordered
    )
    x_ticks = "\n".join(
        (
            f'    <line x1="{_point(x_position(row.noise_multiplier))}" y1="{top + plot_height}" '
            f'x2="{_point(x_position(row.noise_multiplier))}" y2="{top + plot_height + 6}" />'
            f'<text x="{_point(x_position(row.noise_multiplier))}" y="{top + plot_height + 24}" '
            f'class="tick" text-anchor="middle">{row.noise_multiplier:g}</text>'
        )
        for row in ordered
    )
    y_ticks: list[str] = []
    for index in range(5):
        tick_log = y_min + (y_max - y_min) * index / 4
        epsilon = 10**tick_log
        y_coord = y_position(epsilon)
        y_ticks.append(
            f'    <line x1="{left - 6}" y1="{_point(y_coord)}" x2="{left + plot_width}" '
            f'y2="{_point(y_coord)}" class="grid" />'
            f'<text x="{left - 12}" y="{_point(y_coord + 4)}" class="tick" '
            f'text-anchor="end">{epsilon:.3g}</text>'
        )

    metadata_text = ""
    if metadata:
        metadata_text = " · ".join(
            f"{html.escape(str(key))}={html.escape(str(value))}"
            for key, value in sorted(metadata.items())
        )
    safe_title = html.escape(title)
    target_y = y_position(target_epsilon)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">
  <title id="title">{safe_title}</title>
  <desc id="description">Noise multiplier versus epsilon on a logarithmic epsilon axis, with the target privacy budget marked.</desc>
  <style>
    text {{ font-family: system-ui, sans-serif; fill: #172033; }}
    .axis {{ stroke: #334155; stroke-width: 1.5; }}
    .grid {{ stroke: #cbd5e1; stroke-width: 1; }}
    .curve {{ fill: none; stroke: #0369a1; stroke-width: 3; }}
    .target {{ stroke: #b91c1c; stroke-width: 2; stroke-dasharray: 8 5; }}
    .within {{ fill: #16a34a; stroke: #14532d; stroke-width: 1.5; }}
    .over {{ fill: #dc2626; stroke: #7f1d1d; stroke-width: 1.5; }}
    .tick {{ font-size: 12px; }}
    .label {{ font-size: 14px; font-weight: 600; }}
  </style>
  <rect width="100%" height="100%" fill="#ffffff" />
  <text x="{width / 2}" y="32" text-anchor="middle" font-size="22" font-weight="700">{safe_title}</text>
  <text x="{width / 2}" y="54" text-anchor="middle" font-size="12">{metadata_text}</text>
  <g>
{chr(10).join(y_ticks)}
{x_ticks}
    <line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" class="axis" />
    <line x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" y2="{top + plot_height}" class="axis" />
    <line x1="{left}" y1="{_point(target_y)}" x2="{left + plot_width}" y2="{_point(target_y)}" class="target" />
    <text x="{left + plot_width - 4}" y="{_point(target_y - 8)}" text-anchor="end" class="tick">target epsilon={target_epsilon:g}</text>
    <polyline points="{points}" class="curve" />
{circles}
  </g>
  <text x="{left + plot_width / 2}" y="{height - 30}" text-anchor="middle" class="label">Noise multiplier (sigma)</text>
  <text x="22" y="{top + plot_height / 2}" text-anchor="middle" class="label" transform="rotate(-90 22 {top + plot_height / 2})">Epsilon (log scale)</text>
  <g transform="translate({left + 10} {height - 58})">
    <circle cx="0" cy="0" r="5" class="within" /><text x="12" y="4" class="tick">within target</text>
    <circle cx="120" cy="0" r="5" class="over" /><text x="132" y="4" class="tick">over target</text>
  </g>
</svg>
"""


def write_svg(
    output_path: Path,
    rows: list[SweepRow],
    target_epsilon: float,
    title: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Write a rendered SVG, creating parent directories when needed."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_svg(rows, target_epsilon, title, metadata), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plot epsilon versus noise multiplier as a standalone SVG."
    )
    parser.add_argument("--dataset-size", type=int, required=True)
    parser.add_argument("--batch-size", type=int, required=True)
    parser.add_argument("--epochs", type=int, required=True)
    parser.add_argument("--target-epsilon", type=float, default=3.0)
    parser.add_argument("--target-delta", type=float)
    parser.add_argument("--sigmas", type=float, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--title", default="Differential-Privacy Budget Sensitivity")
    args = parser.parse_args()

    target_delta = args.target_delta if args.target_delta is not None else 1.0 / args.dataset_size
    rows = compute_sweep(
        dataset_size=args.dataset_size,
        batch_size=args.batch_size,
        epochs=args.epochs,
        target_epsilon=args.target_epsilon,
        target_delta=target_delta,
        sigma_values=args.sigmas,
    )
    write_svg(
        args.output,
        rows,
        args.target_epsilon,
        args.title,
        {
            "batch": args.batch_size,
            "dataset": args.dataset_size,
            "delta": target_delta,
            "epochs": args.epochs,
        },
    )


if __name__ == "__main__":
    main()
