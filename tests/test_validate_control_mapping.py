"""Tests for the NIST control-mapping validator and JSON report."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

from validate_control_mapping import main, validate, write_json_report  # noqa: E402

FIELDNAMES = [
    "pattern",
    "module",
    "nist_ai_rmf_control",
    "nist_pf_control",
    "nist_csf_2_control",
]


def _write_csv(path: Path, **overrides: str) -> None:
    row = {
        "pattern": "Encrypted processing",
        "module": "fhe-feature-extraction/federated",
        "nist_ai_rmf_control": "MANAGE-2.2",
        "nist_pf_control": "CT.DP-P1",
        "nist_csf_2_control": "PR.DS-01",
    }
    row.update(overrides)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerow(row)


def test_report_represents_success_without_machine_specific_timestamp(tmp_path: Path) -> None:
    source = tmp_path / "mapping.csv"
    destination = tmp_path / "nested" / "report.json"
    _write_csv(source)

    result = validate(source, min_rows=1)
    write_json_report(result, Path("docs/compliance/mapping.csv"), 1, destination)
    report = json.loads(destination.read_text(encoding="utf-8"))

    assert report == {
        "schema_version": "1.0",
        "source": "docs/compliance/mapping.csv",
        "status": "pass",
        "minimum_rows": 1,
        "row_count": 1,
        "error_count": 0,
        "warning_count": 0,
        "errors": [],
        "warnings": [],
    }


def test_report_includes_structured_validation_errors(tmp_path: Path) -> None:
    source = tmp_path / "mapping.csv"
    destination = tmp_path / "report.json"
    _write_csv(source, nist_pf_control="not-a-control")

    result = validate(source, min_rows=2)
    write_json_report(result, source, 2, destination)
    report = json.loads(destination.read_text(encoding="utf-8"))

    assert report["status"] == "fail"
    assert report["row_count"] == 1
    assert report["error_count"] == 2
    assert {error["column"] for error in report["errors"]} == {
        "nist_pf_control",
        "row_count",
    }


def test_cli_writes_report_on_success(tmp_path: Path) -> None:
    source = tmp_path / "mapping.csv"
    destination = tmp_path / "report.json"
    _write_csv(source)

    exit_code = main(
        [
            "--csv",
            str(source),
            "--min-rows",
            "1",
            "--report-json",
            str(destination),
            "--quiet",
        ]
    )

    assert exit_code == 0
    assert json.loads(destination.read_text(encoding="utf-8"))["status"] == "pass"


def test_cli_writes_report_before_returning_failure(tmp_path: Path) -> None:
    source = tmp_path / "mapping.csv"
    destination = tmp_path / "report.json"
    _write_csv(source, nist_ai_rmf_control="")

    exit_code = main(
        [
            "--csv",
            str(source),
            "--min-rows",
            "1",
            "--report-json",
            str(destination),
            "--quiet",
        ]
    )

    assert exit_code == 1
    report = json.loads(destination.read_text(encoding="utf-8"))
    assert report["status"] == "fail"
    assert report["errors"][0]["column"] == "nist_ai_rmf_control"
