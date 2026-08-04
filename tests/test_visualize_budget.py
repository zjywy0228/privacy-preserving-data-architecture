"""Tests for the deterministic differential-privacy budget SVG renderer."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "dp-llm-training"))

from privacy_budget_calculator import SweepRow  # noqa: E402
from visualize_budget import compute_sweep, render_svg, write_svg  # noqa: E402

SAMPLE_ROWS = [
    SweepRow(noise_multiplier=0.5, epsilon=12.0, within_budget=False),
    SweepRow(noise_multiplier=1.0, epsilon=3.0, within_budget=True),
    SweepRow(noise_multiplier=2.0, epsilon=0.8, within_budget=True),
]


def test_computed_epsilon_decreases_as_noise_increases() -> None:
    rows = compute_sweep(
        dataset_size=5000,
        batch_size=64,
        epochs=3,
        target_epsilon=3.0,
        target_delta=1e-5,
        sigma_values=[0.5, 1.0, 2.0],
    )

    assert [row.noise_multiplier for row in rows] == [0.5, 1.0, 2.0]
    assert rows[0].epsilon > rows[1].epsilon > rows[2].epsilon


def test_svg_contains_curve_target_and_accessible_text() -> None:
    svg = render_svg(
        SAMPLE_ROWS,
        target_epsilon=3.0,
        title="Budget sensitivity",
        metadata={"dataset": 5000, "epochs": 3},
    )

    assert svg.startswith("<svg")
    assert "<polyline" in svg
    assert "target epsilon=3" in svg
    assert "within target" in svg
    assert 'aria-labelledby="title description"' in svg


def test_svg_is_deterministic_for_same_input() -> None:
    first = render_svg(SAMPLE_ROWS, 3.0)
    second = render_svg(SAMPLE_ROWS, 3.0)

    assert first == second


def test_svg_escapes_title_and_metadata() -> None:
    svg = render_svg(
        SAMPLE_ROWS,
        3.0,
        title="<Budget & privacy>",
        metadata={"model": "A&B"},
    )

    assert "&lt;Budget &amp; privacy&gt;" in svg
    assert "model=A&amp;B" in svg


def test_write_svg_creates_parent_directory(tmp_path: Path) -> None:
    output = tmp_path / "figures" / "budget.svg"
    write_svg(output, SAMPLE_ROWS, 3.0, "Budget")

    assert output.exists()
    assert "<svg" in output.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"dataset_size": 0},
        {"batch_size": 0},
        {"batch_size": 6000},
        {"epochs": 0},
        {"target_epsilon": 0.0},
        {"target_delta": 0.0},
        {"target_delta": 1.0},
        {"sigma_values": [0.0]},
    ],
)
def test_compute_sweep_rejects_invalid_parameters(kwargs: dict) -> None:
    params = {
        "dataset_size": 5000,
        "batch_size": 64,
        "epochs": 3,
        "target_epsilon": 3.0,
        "target_delta": 1e-5,
        "sigma_values": [0.5, 1.0],
    }
    params.update(kwargs)

    with pytest.raises(ValueError):
        compute_sweep(**params)


def test_render_svg_rejects_empty_or_invalid_rows() -> None:
    with pytest.raises(ValueError, match="At least one"):
        render_svg([], 3.0)
    with pytest.raises(ValueError, match="finite, positive"):
        render_svg(
            [SweepRow(noise_multiplier=1.0, epsilon=0.0, within_budget=True)],
            3.0,
        )
