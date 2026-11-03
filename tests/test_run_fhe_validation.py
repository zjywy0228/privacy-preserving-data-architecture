"""Verify the split-role flag, provenance, and accuracy of run_fhe_validation."""

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "validation"))
import run_fhe_validation  # noqa: E402


def test_parser_accepts_split_roles_flag():
    args = run_fhe_validation._build_parser().parse_args(["--split-roles"])
    assert args.split_roles is True


def test_split_roles_without_tenseal_exits_2(monkeypatch):
    monkeypatch.setattr(run_fhe_validation.split_roles, "TENSEAL_AVAILABLE", False)
    with pytest.raises(SystemExit) as excinfo:
        run_fhe_validation.main(["--split-roles"])
    assert excinfo.value.code == 2


def test_split_roles_validation_is_accurate():
    pytest.importorskip("tenseal")
    result = run_fhe_validation.validate_split_roles(
        n_samples=3, signal_dim=32, feature_dim=4, seed=0
    )
    assert result["mean_error"] < 1e-4
    assert result["max_error"] < 1e-3
    assert result["evaluator_has_secret_key"] is False


def test_json_report_includes_provenance(tmp_path):
    output = tmp_path / "r.json"
    run_fhe_validation.main(
        [
            "--n-samples",
            "3",
            "--signal-dim",
            "16",
            "--feature-dim",
            "4",
            "--output",
            str(output),
        ]
    )
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["schema_version"] == "1.1"
    assert report["provenance"]["run_mode"] in {"mock", "measured"}
