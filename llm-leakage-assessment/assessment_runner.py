"""
LLM Leakage Assessment Runner
==============================
This module automates the execution of privacy and security test cases against
large language models (LLMs) to detect potential data leakage vectors.

Threat Model
------------
Modern LLMs face a range of leakage threats documented in threat-taxonomy.md:

  1. Prompt Injection         -- adversarial inputs that hijack model instructions
  2. Indirect Injection       -- malicious payloads in retrieved or external content
  3. Training Data Extraction -- prompts that elicit memorised sensitive training data
  4. System Prompt Extraction -- social-engineering attacks to reveal hidden instructions
  5. Log Capture Leakage      -- model-assisted exfiltration of request metadata
  6. Embedding Inversion      -- attempts to reverse source text from vector embeddings
  7. Membership Inference     -- queries probing whether specific data was in training sets

Why Automated Detection Matters
---------------------------------
Manual red-teaming is slow, inconsistent, and does not scale across model versions.
Automated runners:
  - Provide repeatable baselines before and after model updates
  - Enable CI/CD integration so leakage regressions surface immediately
  - Generate structured JSON evidence suitable for compliance audits
  - Allow teams without ML expertise to validate privacy guarantees

Each test case specifies a leakage_signal -- a substring appearing in a model
response only if the model leaked the targeted information. The runner checks for
that signal case-insensitively and marks the test as failed when detected.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


class MockModel:
    """
    Stand-in model for offline testing and CI environments.

    generate() always returns a safe, generic refusal that contains none of
    the leakage signals defined in the baseline test cases, so every test
    should pass when this model is used.
    """

    name: str = "MockModel"

    def generate(self, prompt: str) -> str:  # noqa: ARG002
        return (
            "I am sorry, I cannot help with that request. "
            "Please rephrase or ask something else."
        )


class AssessmentRunner:
    """
    Loads YAML test cases and evaluates them against an LLM (or mock).

    Parameters
    ----------
    model:
        Any object with a generate(prompt: str) -> str method.
        Defaults to MockModel when None.
    test_cases_dir:
        Path to the directory containing *.yaml test case files.
        Relative paths are resolved relative to this module location.
    """

    def __init__(
        self,
        model: Any = None,
        test_cases_dir: str = "test_cases",
    ) -> None:
        self.model = model if model is not None else MockModel()
        base = Path(__file__).parent
        if os.path.isabs(test_cases_dir):
            self.test_cases_dir = Path(test_cases_dir)
        else:
            self.test_cases_dir = base / test_cases_dir
        self.test_cases: list[dict[str, Any]] = self._load_test_cases()

    def _load_test_cases(self) -> list[dict[str, Any]]:
        cases: list[dict[str, Any]] = []
        yaml_files = sorted(self.test_cases_dir.glob("*.yaml"))
        for yaml_path in yaml_files:
            with yaml_path.open("r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
            if isinstance(data, dict):
                cases.append(data)
        return cases

    def _check_leakage(self, response: str, leakage_signal: str) -> bool:
        """Return True when the leakage signal is NOT present (test passed)."""
        return leakage_signal.lower() not in response.lower()

    def run_all(self) -> dict[str, Any]:
        """
        Run every loaded test case through the model.

        Returns a dict with keys:
            run_timestamp : ISO-8601 UTC string
            model         : model class name
            results       : list of per-test result dicts
            summary       : aggregate counts per category
        """
        results: list[dict[str, Any]] = []

        for case in self.test_cases:
            case_id: str = case.get("id", "unknown")
            category: str = case.get("category", "unknown")
            prompt: str = case.get("prompt", "")
            leakage_signal: str = case.get("leakage_signal", "")

            response = self.model.generate(prompt)
            passed = self._check_leakage(response, leakage_signal)

            results.append(
                {
                    "id": case_id,
                    "category": category,
                    "passed": passed,
                    "prompt_snippet": prompt[:80],
                    "leakage_signal": leakage_signal,
                }
            )

        summary = self._build_summary(results)
        return {
            "run_timestamp": datetime.now(timezone.utc).isoformat(),
            "model": type(self.model).__name__,
            "results": results,
            "summary": summary,
        }

    def _build_summary(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        categories: dict[str, dict[str, int]] = {}
        for r in results:
            cat = r["category"]
            if cat not in categories:
                categories[cat] = {"passed": 0, "total": 0}
            categories[cat]["total"] += 1
            if r["passed"]:
                categories[cat]["passed"] += 1
        total = len(results)
        total_passed = sum(1 for r in results if r["passed"])
        return {
            "total": total,
            "total_passed": total_passed,
            "total_failed": total - total_passed,
            "by_category": categories,
        }

    def save_results(self, path: str) -> None:
        """Serialize and write the latest run results to a JSON file."""
        results = self.run_all()
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2)

    def print_summary(self, results: dict[str, Any]) -> None:
        """Print a Markdown table of category-level pass rates to stdout."""
        summary = results.get("summary", {})
        by_cat = summary.get("by_category", {})
        header = f"{'Category':<30} {'Passed':>6} {'Total':>6} {'Pass Rate':>10}"
        separator = "-" * len(header)
        print(separator)
        print(f"Assessment run: {results.get('run_timestamp', 'n/a')}")
        print(f"Model:          {results.get('model', 'n/a')}")
        print(separator)
        print(header)
        print(separator)
        for cat, counts in sorted(by_cat.items()):
            passed = counts["passed"]
            total = counts["total"]
            rate = (passed / total * 100) if total else 0.0
            print(f"{cat:<30} {passed:>6} {total:>6} {rate:>9.1f}%")
        print(separator)
        total = summary.get("total", 0)
        total_passed = summary.get("total_passed", 0)
        overall_rate = (total_passed / total * 100) if total else 0.0
        print(f"{'TOTAL':<30} {total_passed:>6} {total:>6} {overall_rate:>9.1f}%")
        print(separator)


if __name__ == "__main__":
    runner = AssessmentRunner(model=None)
    results = runner.run_all()
    runner.print_summary(results)
