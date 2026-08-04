"""Tests for the data-minimized leakage-assessment report generator."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "llm-leakage-assessment"))

from report_generator import render_html, render_markdown, write_report  # noqa: E402


@pytest.fixture
def assessment_payload() -> dict:
    return {
        "run_timestamp": "2026-08-03T12:00:00+00:00",
        "model": "Synthetic<Model>",
        "results": [
            {
                "id": "PI-001",
                "category": "Prompt injection",
                "passed": True,
                "prompt_snippet": "sensitive prompt text",
                "leakage_signal": "secret-canary",
            },
            {
                "id": "MI-001",
                "category": "Membership inference",
                "passed": False,
                "prompt_snippet": "another sensitive prompt",
                "leakage_signal": "private-member",
            },
        ],
    }


def test_markdown_has_summary_and_omits_sensitive_fields(
    assessment_payload: dict,
) -> None:
    report = render_markdown(assessment_payload)

    assert "1 / 2" in report
    assert "50.0%" in report
    assert "MI-001" in report
    assert "sensitive prompt text" not in report
    assert "secret-canary" not in report


def test_html_escapes_metadata_and_omits_sensitive_fields(
    assessment_payload: dict,
) -> None:
    report = render_html(assessment_payload, title="<Assessment>")

    assert "&lt;Assessment&gt;" in report
    assert "Synthetic&lt;Model&gt;" in report
    assert "private-member" not in report
    assert 'class="fail"' in report


def test_empty_results_have_zero_rate() -> None:
    report = render_markdown(
        {
            "run_timestamp": "2026-08-03T12:00:00+00:00",
            "model": "MockModel",
            "results": [],
        }
    )

    assert "0 / 0" in report
    assert "0.0%" in report


@pytest.mark.parametrize("suffix", [".md", ".html"])
def test_write_report_creates_supported_outputs(
    assessment_payload: dict, tmp_path: Path, suffix: str
) -> None:
    input_path = tmp_path / "results.json"
    output_path = tmp_path / "reports" / f"assessment{suffix}"
    input_path.write_text(json.dumps(assessment_payload), encoding="utf-8")

    write_report(input_path, output_path, "Synthetic assessment")

    assert output_path.exists()
    assert "Synthetic assessment" in output_path.read_text(encoding="utf-8")


def test_write_report_rejects_unknown_output_type(assessment_payload: dict, tmp_path: Path) -> None:
    input_path = tmp_path / "results.json"
    input_path.write_text(json.dumps(assessment_payload), encoding="utf-8")

    with pytest.raises(ValueError, match="Output path"):
        write_report(input_path, tmp_path / "report.txt", "Assessment")


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"results": ["not-an-object"]},
        {"results": [{"id": "", "category": "x", "passed": True}]},
        {"results": [{"id": "x", "category": "", "passed": True}]},
        {"results": [{"id": "x", "category": "y", "passed": "yes"}]},
    ],
)
def test_invalid_payloads_are_rejected(payload: dict) -> None:
    with pytest.raises(ValueError):
        render_markdown(payload)
