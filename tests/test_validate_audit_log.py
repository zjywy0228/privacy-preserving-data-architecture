"""
Tests for dp-llm-training/validate_audit_log.py

All tests are self-contained; no network, GPU, or ML framework required.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "dp-llm-training"))

from validate_audit_log import ValidationResult, validate_log  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_GOOD_META = {
    "target_epsilon": 3.0,
    "target_delta": 1e-5,
    "noise_multiplier": 1.1,
    "sample_rate": 0.01,
}

_GOOD_EPOCH = {
    "epoch": 1,
    "cumulative_steps": 100,
    "epsilon_spent": 1.2,
    "delta": 1e-5,
    "loss": 0.45,
    "budget_fraction": round(1.2 / 3.0, 6),
    "budget_exhausted": False,
}


def _write_log(data: dict, tmp_dir: str) -> str:
    path = str(Path(tmp_dir) / "audit.json")
    Path(path).write_text(json.dumps(data), encoding="utf-8")
    return path


def _good_log(n_epochs: int = 3) -> dict:
    meta = dict(_GOOD_META)
    log = []
    eps_per_epoch = 0.8
    for i in range(1, n_epochs + 1):
        eps = round(eps_per_epoch * i, 6)
        log.append(
            {
                "epoch": i,
                "cumulative_steps": i * 100,
                "epsilon_spent": eps,
                "delta": 1e-5,
                "loss": round(0.5 - i * 0.02, 6),
                "budget_fraction": round(min(eps / meta["target_epsilon"], 1.0), 6),
                "budget_exhausted": eps >= meta["target_epsilon"],
            }
        )
    return {"metadata": meta, "log": log}


# ---------------------------------------------------------------------------
# Structural tests
# ---------------------------------------------------------------------------


class TestStructuralValidation(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.mkdtemp()

    def test_valid_log_passes(self) -> None:
        path = _write_log(_good_log(), self._tmp)
        result = validate_log(path)
        self.assertTrue(result.passed, result.errors)
        self.assertEqual(result.errors, [])

    def test_missing_file(self) -> None:
        result = validate_log("/tmp/nonexistent_ppda_audit_abc123.json")
        self.assertFalse(result.passed)
        self.assertTrue(any("Cannot read" in e for e in result.errors))

    def test_invalid_json(self) -> None:
        path = str(Path(self._tmp) / "bad.json")
        Path(path).write_text("not json {{{", encoding="utf-8")
        result = validate_log(path)
        self.assertFalse(result.passed)
        self.assertTrue(any("Invalid JSON" in e for e in result.errors))

    def test_missing_metadata_key(self) -> None:
        data = _good_log()
        del data["metadata"]
        path = _write_log(data, self._tmp)
        result = validate_log(path)
        self.assertFalse(result.passed)
        self.assertTrue(any("metadata" in e for e in result.errors))

    def test_missing_log_key(self) -> None:
        data = _good_log()
        del data["log"]
        path = _write_log(data, self._tmp)
        result = validate_log(path)
        self.assertFalse(result.passed)
        self.assertTrue(any("log" in e for e in result.errors))

    def test_empty_log_array(self) -> None:
        data = _good_log()
        data["log"] = []
        path = _write_log(data, self._tmp)
        result = validate_log(path)
        self.assertFalse(result.passed)
        self.assertTrue(any("at least one" in e for e in result.errors))


# ---------------------------------------------------------------------------
# Metadata validation tests
# ---------------------------------------------------------------------------


class TestMetadataValidation(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.mkdtemp()

    def _log_with_meta(self, **overrides: object) -> dict:
        data = _good_log(1)
        data["metadata"].update(overrides)
        return data

    def test_negative_epsilon_fails(self) -> None:
        path = _write_log(self._log_with_meta(target_epsilon=-1.0), self._tmp)
        result = validate_log(path)
        self.assertFalse(result.passed)
        self.assertTrue(any("target_epsilon" in e for e in result.errors))

    def test_zero_noise_multiplier_fails(self) -> None:
        path = _write_log(self._log_with_meta(noise_multiplier=0), self._tmp)
        result = validate_log(path)
        self.assertFalse(result.passed)

    def test_delta_gte_one_fails(self) -> None:
        path = _write_log(self._log_with_meta(target_delta=1.0), self._tmp)
        result = validate_log(path)
        self.assertFalse(result.passed)
        self.assertTrue(any("target_delta" in e for e in result.errors))

    def test_sample_rate_gt_one_fails(self) -> None:
        path = _write_log(self._log_with_meta(sample_rate=1.5), self._tmp)
        result = validate_log(path)
        self.assertFalse(result.passed)

    def test_large_epsilon_warning_in_normal_mode(self) -> None:
        path = _write_log(self._log_with_meta(target_epsilon=15.0), self._tmp)
        # Also fix log entry to match new target_epsilon
        data = self._log_with_meta(target_epsilon=15.0)
        eps = data["log"][0]["epsilon_spent"]
        data["log"][0]["budget_fraction"] = round(eps / 15.0, 6)
        data["log"][0]["budget_exhausted"] = eps >= 15.0
        path = _write_log(data, self._tmp)
        result = validate_log(path)
        self.assertTrue(result.passed)
        self.assertTrue(any("large" in w for w in result.warnings))

    def test_large_epsilon_error_in_strict_mode(self) -> None:
        data = self._log_with_meta(target_epsilon=15.0)
        eps = data["log"][0]["epsilon_spent"]
        data["log"][0]["budget_fraction"] = round(eps / 15.0, 6)
        data["log"][0]["budget_exhausted"] = eps >= 15.0
        path = _write_log(data, self._tmp)
        result = validate_log(path, strict=True)
        self.assertFalse(result.passed)
        self.assertTrue(any("large" in e for e in result.errors))


# ---------------------------------------------------------------------------
# Epoch record validation tests
# ---------------------------------------------------------------------------


class TestEpochValidation(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.mkdtemp()

    def _log_with_epoch_patch(self, **overrides: object) -> dict:
        data = _good_log(2)
        data["log"][1].update(overrides)
        return data

    def test_non_monotonic_epoch_fails(self) -> None:
        data = _good_log(3)
        data["log"][2]["epoch"] = 2  # duplicate epoch number
        path = _write_log(data, self._tmp)
        result = validate_log(path)
        self.assertFalse(result.passed)
        self.assertTrue(any("monotonically" in e for e in result.errors))

    def test_decreasing_steps_fails(self) -> None:
        data = _good_log(2)
        data["log"][1]["cumulative_steps"] = 50  # less than epoch 1's 100
        path = _write_log(data, self._tmp)
        result = validate_log(path)
        self.assertFalse(result.passed)

    def test_decreasing_epsilon_fails(self) -> None:
        data = _good_log(2)
        data["log"][1]["epsilon_spent"] = 0.1  # less than epoch 1's 0.8
        # Also fix budget_fraction/exhausted to avoid double-error
        data["log"][1]["budget_fraction"] = round(0.1 / 3.0, 6)
        data["log"][1]["budget_exhausted"] = False
        path = _write_log(data, self._tmp)
        result = validate_log(path)
        self.assertFalse(result.passed)
        self.assertTrue(any("non-decreasing" in e for e in result.errors))

    def test_wrong_budget_fraction_fails(self) -> None:
        data = _good_log(1)
        data["log"][0]["budget_fraction"] = 0.99  # wrong
        path = _write_log(data, self._tmp)
        result = validate_log(path)
        self.assertFalse(result.passed)
        self.assertTrue(any("budget_fraction" in e for e in result.errors))

    def test_wrong_budget_exhausted_fails(self) -> None:
        data = _good_log(1)
        data["log"][0]["budget_exhausted"] = True  # wrong (1.2 < 3.0)
        path = _write_log(data, self._tmp)
        result = validate_log(path)
        self.assertFalse(result.passed)
        self.assertTrue(any("budget_exhausted" in e for e in result.errors))

    def test_missing_epoch_field_fails(self) -> None:
        data = _good_log(1)
        del data["log"][0]["loss"]
        path = _write_log(data, self._tmp)
        result = validate_log(path)
        self.assertFalse(result.passed)

    def test_string_epoch_number_fails(self) -> None:
        data = _good_log(1)
        data["log"][0]["epoch"] = "one"
        path = _write_log(data, self._tmp)
        result = validate_log(path)
        self.assertFalse(result.passed)


# ---------------------------------------------------------------------------
# ValidationResult string formatting
# ---------------------------------------------------------------------------


class TestValidationResult(unittest.TestCase):
    def test_pass_format(self) -> None:
        r = ValidationResult(path="audit.json", passed=True)
        self.assertIn("[PASS]", str(r))

    def test_fail_format(self) -> None:
        r = ValidationResult(path="audit.json", passed=False, errors=["bad field"])
        s = str(r)
        self.assertIn("[FAIL]", s)
        self.assertIn("ERROR", s)
        self.assertIn("bad field", s)

    def test_warning_format(self) -> None:
        r = ValidationResult(path="audit.json", passed=True, warnings=["heads up"])
        self.assertIn("WARNING", str(r))


if __name__ == "__main__":
    unittest.main()
