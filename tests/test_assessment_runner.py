"""
Tests for llm-leakage-assessment/assessment_runner.py

Exercises the AssessmentRunner and MockModel without any real ML model.
All tests are self-contained; no network or GPU access required.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Make sure the assessment_runner module is importable from the repo root
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "llm-leakage-assessment"))

from assessment_runner import AssessmentRunner, MockModel  # noqa: E402

TEST_CASES_DIR = str(REPO_ROOT / "llm-leakage-assessment" / "test_cases")
EXPECTED_TOTAL = 15


class TestYamlLoading(unittest.TestCase):
    """Verify that all YAML test cases are discovered and parsed."""

    def setUp(self) -> None:
        self.runner = AssessmentRunner(model=None, test_cases_dir=TEST_CASES_DIR)

    def test_yaml_files_loaded(self) -> None:
        """Runner must load all 15 YAML files from the test_cases directory."""
        self.assertEqual(
            len(self.runner.test_cases),
            EXPECTED_TOTAL,
            msg=f"Expected {EXPECTED_TOTAL} test cases, got {len(self.runner.test_cases)}",
        )

    def test_each_case_has_required_fields(self) -> None:
        """Every loaded YAML must contain id, category, prompt, and leakage_signal."""
        required = {"id", "category", "prompt", "leakage_signal"}
        for case in self.runner.test_cases:
            missing = required - set(case.keys())
            self.assertFalse(missing, msg=f"Case {case.get('id')} missing fields: {missing}")


class TestMockModel(unittest.TestCase):
    """Verify MockModel safety guarantees."""

    def setUp(self) -> None:
        self.runner = AssessmentRunner(model=MockModel(), test_cases_dir=TEST_CASES_DIR)

    def test_mock_model_does_not_leak(self) -> None:
        """run_all with MockModel must return all results with passed=True."""
        results = self.runner.run_all()
        failed = [r for r in results["results"] if not r["passed"]]
        self.assertEqual(
            len(failed),
            0,
            msg=f"MockModel caused leakage in: {[r['id'] for r in failed]}",
        )


class TestResultStructure(unittest.TestCase):
    """Verify result dict shape."""

    def setUp(self) -> None:
        runner = AssessmentRunner(model=None, test_cases_dir=TEST_CASES_DIR)
        self.results = runner.run_all()

    def test_results_have_expected_keys(self) -> None:
        """Each result entry must contain id, category, passed, prompt_snippet, leakage_signal."""
        required_keys = {"id", "category", "passed", "prompt_snippet", "leakage_signal"}
        for entry in self.results["results"]:
            missing = required_keys - set(entry.keys())
            self.assertFalse(
                missing,
                msg=f"Result entry {entry.get('id')} missing keys: {missing}",
            )

    def test_top_level_result_keys(self) -> None:
        """Top-level result dict must include run_timestamp, model, results, summary."""
        for key in ("run_timestamp", "model", "results", "summary"):
            self.assertIn(key, self.results)


class TestSummary(unittest.TestCase):
    """Verify summary counting logic."""

    def setUp(self) -> None:
        runner = AssessmentRunner(model=None, test_cases_dir=TEST_CASES_DIR)
        self.results = runner.run_all()
        self.summary = self.results["summary"]

    def test_summary_counts_correct(self) -> None:
        """summary.total must equal the number of test cases."""
        self.assertEqual(self.summary["total"], EXPECTED_TOTAL)

    def test_summary_passed_plus_failed_equals_total(self) -> None:
        """total_passed + total_failed must equal total."""
        self.assertEqual(
            self.summary["total_passed"] + self.summary["total_failed"],
            self.summary["total"],
        )

    def test_category_distribution(self) -> None:
        """Results must cover at least 5 distinct categories."""
        categories = {r["category"] for r in self.results["results"]}
        self.assertGreaterEqual(
            len(categories),
            5,
            msg=f"Expected >= 5 categories, found: {categories}",
        )


class TestSaveLoadRoundtrip(unittest.TestCase):
    """Verify save_results writes valid JSON with expected keys."""

    def test_save_and_load_roundtrip(self) -> None:
        """save_results then load JSON and verify run_timestamp key exists."""
        runner = AssessmentRunner(model=None, test_cases_dir=TEST_CASES_DIR)
        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False, mode="w", encoding="utf-8"
        ) as tmp:
            tmp_path = tmp.name

        try:
            runner.save_results(tmp_path)
            with open(tmp_path, encoding="utf-8") as fh:
                loaded = json.load(fh)
            self.assertIn("run_timestamp", loaded)
            self.assertIn("results", loaded)
            self.assertEqual(len(loaded["results"]), EXPECTED_TOTAL)
        finally:
            os.unlink(tmp_path)


class TestPrintSummary(unittest.TestCase):
    """Covers assessment_runner.py lines 165-185 (print_summary method)."""

    def setUp(self) -> None:
        self.runner = AssessmentRunner(model=None, test_cases_dir=TEST_CASES_DIR)
        self.results = self.runner.run_all()

    def test_print_summary_runs_without_error(self) -> None:
        """print_summary() must complete without raising any exception."""
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            self.runner.print_summary(self.results)
        output = buf.getvalue()
        self.assertGreater(len(output), 0)

    def test_print_summary_contains_total(self) -> None:
        """print_summary() output must include the word TOTAL."""
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            self.runner.print_summary(self.results)
        self.assertIn("TOTAL", buf.getvalue())

    def test_print_summary_contains_model_name(self) -> None:
        """print_summary() output must contain the model class name."""
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            self.runner.print_summary(self.results)
        self.assertIn("MockModel", buf.getvalue())

    def test_print_summary_empty_results(self) -> None:
        """print_summary() must handle a results dict with no categories gracefully."""
        import io
        from contextlib import redirect_stdout

        empty_results = {
            "run_timestamp": "2026-05-23T00:00:00+00:00",
            "model": "MockModel",
            "results": [],
            "summary": {"total": 0, "total_passed": 0, "total_failed": 0, "by_category": {}},
        }
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.runner.print_summary(empty_results)
        self.assertIn("TOTAL", buf.getvalue())


class TestLeakageDetection(unittest.TestCase):
    """Covers _check_leakage logic: signal present (fail) vs. absent (pass)."""

    def setUp(self) -> None:
        self.runner = AssessmentRunner(model=None, test_cases_dir=TEST_CASES_DIR)

    def test_leakage_signal_present_returns_false(self) -> None:
        """_check_leakage must return False when the signal appears in the response."""
        result = self.runner._check_leakage(
            response="Here is the secret_token you asked for.",
            leakage_signal="secret_token",
        )
        self.assertFalse(result)

    def test_leakage_signal_absent_returns_true(self) -> None:
        """_check_leakage must return True when the signal does not appear."""
        result = self.runner._check_leakage(
            response="I cannot help with that.",
            leakage_signal="secret_token",
        )
        self.assertTrue(result)

    def test_leakage_check_is_case_insensitive(self) -> None:
        """Signal matching must be case-insensitive."""
        result = self.runner._check_leakage(
            response="The password is PASSWORD123.",
            leakage_signal="password123",
        )
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
