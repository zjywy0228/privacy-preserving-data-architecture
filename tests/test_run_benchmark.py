"""Tests for reproducible FHE benchmark reports."""

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "run_benchmark", REPO_ROOT / "fhe-feature-extraction/benchmarks/run_benchmark.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
sys.path.insert(0, str(REPO_ROOT / "tools"))
from validate_dashboard_data import validate_benchmark  # noqa: E402


def test_summarize_ms_known_values():
    assert module.summarize_ms([1.0, 2.0, 3.0, 10.0]) == {
        "median": 2.5,
        "mean": 4.0,
        "min": 1.0,
        "max": 10.0,
    }


def test_summarize_ms_rejects_empty():
    with pytest.raises(ValueError, match="no timing samples"):
        module.summarize_ms([])


def test_make_projection_is_deterministic_with_unit_rows():
    projection = module.make_projection(16, 4, 1)
    np.testing.assert_array_equal(projection, module.make_projection(16, 4, 1))
    np.testing.assert_allclose(np.linalg.norm(projection, axis=1), 1, atol=1e-12, rtol=0)


def test_mock_run_measures_cleartext_only():
    report = module.run_benchmark(
        [16], trials=3, warmup=1, feature_dim=4, seed=1, use_tenseal=False
    )
    assert report["mode"] == "mock"
    assert report["rows"][0]["encrypted_ms"] is None
    assert report["rows"][0]["cleartext_ms"]["median"] >= 0
    assert report["provenance"]["run_mode"] == "mock"


def test_require_tenseal_raises_when_unavailable(monkeypatch):
    monkeypatch.setattr(module, "TENSEAL_AVAILABLE", False)
    with pytest.raises(RuntimeError, match="TenSEAL is required"):
        module.run_benchmark(use_tenseal=True)


def test_render_markdown_mock_says_not_measured():
    report = module.run_benchmark([16], trials=3, feature_dim=4, use_tenseal=False)
    markdown = module.render_markdown(report)
    assert "not measured" in markdown
    assert "mock" in markdown


def test_to_dashboard_rejects_mock_report():
    report = module.run_benchmark([16], trials=3, feature_dim=4, use_tenseal=False)
    with pytest.raises(ValueError, match="dashboard data requires a TenSEAL run"):
        module.to_dashboard(report)


def test_main_refuses_dashboard_in_mock_mode(monkeypatch, tmp_path):
    monkeypatch.setattr(module, "TENSEAL_AVAILABLE", False)
    assert (
        module.main(
            [
                "--sizes",
                "16",
                "--trials",
                "2",
                "--feature-dim",
                "4",
                "--output-dir",
                str(tmp_path),
                "--write-dashboard",
                "--dashboard-path",
                str(tmp_path / "b.json"),
            ]
        )
        == 2
    )
    assert not (tmp_path / "b.json").exists()


def test_real_tenseal_run_matches_plaintext():
    pytest.importorskip("tenseal")
    report = module.run_benchmark([128], trials=3, warmup=1, feature_dim=8, seed=0)
    assert report["rows"][0]["encrypted_ms"]["median"] > 0
    assert report["rows"][0]["max_abs_error"] < 1e-3
    assert validate_benchmark(module.to_dashboard(report)) == []


def test_split_benchmark_requires_tenseal(monkeypatch):
    monkeypatch.setattr(module.split_roles, "TENSEAL_AVAILABLE", False)
    with pytest.raises(RuntimeError, match="TenSEAL is required for split-role timings"):
        module.run_split_benchmark([16], trials=2, warmup=0, feature_dim=4)
    with pytest.raises(RuntimeError, match="split-role timings require TenSEAL"):
        module.run_benchmark([16], feature_dim=4, use_tenseal=False, include_split_roles=True)


def test_split_benchmark_stage_timings():
    pytest.importorskip("tenseal")
    rows = module.run_split_benchmark([64], trials=2, warmup=1, feature_dim=4, seed=0)
    row = rows[0]
    assert all(stage["median"] > 0 for stage in row["stages_ms"].values())
    assert row["stages_ms"]["total"]["median"] >= row["stages_ms"]["evaluate"]["median"]
    assert row["max_abs_error"] < 1e-3


def test_render_markdown_includes_split_table():
    report = module.run_benchmark([16], trials=3, warmup=0, feature_dim=4, use_tenseal=False)
    report["split_roles"] = [
        {
            "vector_size": 16,
            "feature_dim": 4,
            "trials": 3,
            "stages_ms": {
                stage: {"median": 1.0, "mean": 1.0, "min": 1.0, "max": 1.0}
                for stage in ("encrypt", "evaluate", "decrypt", "total")
            },
            "input_ciphertext_bytes": 2048,
            "feature_ciphertext_bytes": 1024,
            "max_abs_error": 0.0,
        }
    ]
    markdown = module.render_markdown(report)
    assert "Split-role stage timings" in markdown
    assert "| 16 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0 | 0 |" in markdown
    assert "--require-tenseal --split-roles" in markdown
