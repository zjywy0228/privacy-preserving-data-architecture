"""Tests for the tools/validate_dashboard_data.py validator."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

from validate_dashboard_data import (  # noqa: E402
    main,
    validate_benchmark,
    validate_directory,
    validate_leakage,
)


def _benchmark() -> dict[str, Any]:
    return {
        "scheme": "CKKS (TenSEAL)",
        "rows": [
            {"vector_size": 128, "cleartext_ms": 0.42, "ciphertext_ms": 18.7},
            {"vector_size": 512, "cleartext_ms": 1.61, "ciphertext_ms": 71.3},
        ],
        "provenance": {
            "run_mode": "archived_record",
            "source": "results.md",
            "note": "reference values",
        },
    }


def _leakage() -> dict[str, Any]:
    return {
        "categories": [
            {"name": "Prompt injection", "passed": 4, "total": 5},
            {"name": "Log-capture leakage", "passed": 2, "total": 2},
        ],
        "provenance": {
            "run_mode": "illustrative_sample",
            "source": "example",
            "note": "layout",
        },
    }


def _measured() -> dict[str, Any]:
    return {
        "run_mode": "measured",
        "source_commit": "abcdef1",
        "generated_at": "2026-10-14T12:00:00+00:00",
        "generator": "fhe-feature-extraction/benchmarks/run_benchmark.py",
    }


def test_repository_dashboard_data_is_valid() -> None:
    """The committed dashboard-data files pass validation."""
    assert validate_directory(REPO_ROOT / "docs" / "assets" / "data") == []


def test_benchmark_without_provenance_is_rejected() -> None:
    """A benchmark file without a provenance block is rejected."""
    data = _benchmark()
    del data["provenance"]
    errors = validate_benchmark(data)
    assert any("provenance" in error for error in errors)


def test_benchmark_sizes_must_increase() -> None:
    """Benchmark rows with non-increasing vector_size are rejected."""
    data = _benchmark()
    data["rows"] = list(reversed(data["rows"]))
    errors = validate_benchmark(data)
    assert any("vector_size" in error for error in errors)


def test_benchmark_timings_must_be_positive() -> None:
    """A zero ciphertext_ms is rejected."""
    data = _benchmark()
    data["rows"][0]["ciphertext_ms"] = 0
    errors = validate_benchmark(data)
    assert any("ciphertext_ms" in error for error in errors)


def test_measured_benchmark_requires_trials() -> None:
    """A measured benchmark without `trials` is rejected."""
    data = _benchmark()
    data["provenance"] = _measured()
    data["platform"] = "x86_64"
    errors = validate_benchmark(data)
    assert any("trials" in error for error in errors)


def test_measured_provenance_requires_commit() -> None:
    """A measured provenance block without source_commit is rejected."""
    data = _benchmark()
    provenance = _measured()
    del provenance["source_commit"]
    data["provenance"] = provenance
    data["trials"] = 5
    data["statistic"] = "median"
    data["platform"] = "x86_64"
    errors = validate_benchmark(data)
    assert any("source_commit" in error for error in errors)


def test_leakage_passed_cannot_exceed_total() -> None:
    """A category with passed > total is rejected."""
    data = _leakage()
    data["categories"][0]["passed"] = 6
    data["categories"][0]["total"] = 5
    errors = validate_leakage(data)
    assert any("passed" in error for error in errors)


def test_leakage_duplicate_category_rejected() -> None:
    """Two categories with the same name are rejected."""
    data = _leakage()
    data["categories"][1]["name"] = "Prompt injection"
    errors = validate_leakage(data)
    assert any("duplicate" in error for error in errors)


def test_leakage_unknown_run_mode_rejected() -> None:
    """A leakage file with an unknown run_mode is rejected."""
    data = _leakage()
    data["provenance"]["run_mode"] = "guess"
    errors = validate_leakage(data)
    assert any("run_mode" in error for error in errors)


def test_fixture_leakage_requires_model_id() -> None:
    """A synthetic_fixture leakage file without model_id is rejected."""
    data = _leakage()
    provenance = _measured()
    provenance["run_mode"] = "synthetic_fixture"
    data["provenance"] = provenance
    errors = validate_leakage(data)
    assert any("model_id" in error for error in errors)


def test_main_reports_failure_and_writes_json(tmp_path: Path) -> None:
    """main() returns 1 and writes a fail report for an invalid directory."""
    bad_benchmark = _benchmark()
    bad_benchmark["rows"] = []
    (tmp_path / "benchmark.json").write_text(json.dumps(bad_benchmark), encoding="utf-8")
    (tmp_path / "leakage-results.json").write_text(json.dumps(_leakage()), encoding="utf-8")
    report_path = tmp_path / "r.json"

    exit_code = main(
        [
            "--data-dir",
            str(tmp_path),
            "--report-json",
            str(report_path),
        ]
    )
    assert exit_code == 1
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "fail"


def test_main_passes_on_valid_files(tmp_path: Path) -> None:
    """main() returns 0 for valid dashboard-data files."""
    (tmp_path / "benchmark.json").write_text(json.dumps(_benchmark()), encoding="utf-8")
    (tmp_path / "leakage-results.json").write_text(json.dumps(_leakage()), encoding="utf-8")

    exit_code = main(["--data-dir", str(tmp_path)])
    assert exit_code == 0
