"""Validate leakage case files before an assessment can call a model."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "llm-leakage-assessment"))

from assessment_runner import (  # noqa: E402
    ALLOWED_CATEGORIES,
    AssessmentRunner,
    CaseValidationError,
    validate_case,
)


def _write_case(directory: Path, name: str, **overrides: str) -> None:
    case = {
        "id": "pi_001",
        "category": "prompt_injection",
        "prompt": "Synthetic prompt",
        "expected_behavior": "Refuse",
        "leakage_signal": "synthetic marker",
    }
    case.update(overrides)
    (directory / name).write_text(yaml.safe_dump(case), encoding="utf-8")


def test_repository_cases_are_valid() -> None:
    """Load all shipped cases with unique identifiers and supported categories."""
    runner = AssessmentRunner()
    assert len(runner.test_cases) == 15
    assert len({case["id"] for case in runner.test_cases}) == 15
    assert all(case["category"] in ALLOWED_CATEGORIES for case in runner.test_cases)

    original = {name: f"  {value}  " for name, value in runner.test_cases[0].items()}
    normalized = validate_case(original, "padded.yaml")
    assert normalized == runner.test_cases[0]
    assert normalized is not original
    assert original["id"].startswith("  ")


@pytest.mark.parametrize(
    "field", ["id", "category", "prompt", "expected_behavior", "leakage_signal"]
)
@pytest.mark.parametrize("invalid_value", [None, 0, False, [], {}])
def test_missing_field_is_rejected(tmp_path: Path, field: str, invalid_value: object) -> None:
    """Reject missing required fields and values that are not strings."""
    case = {
        "id": "pi_001",
        "category": "prompt_injection",
        "prompt": "Synthetic prompt",
        "expected_behavior": "Refuse",
        "leakage_signal": "synthetic marker",
    }
    del case[field]
    path = tmp_path / "missing.yaml"
    path.write_text(yaml.safe_dump(case), encoding="utf-8")
    with pytest.raises(CaseValidationError, match=rf"missing.yaml: field '{field}'"):
        AssessmentRunner(test_cases_dir=str(tmp_path))

    path.write_text(yaml.safe_dump({**case, field: invalid_value}), encoding="utf-8")
    with pytest.raises(CaseValidationError, match=rf"missing.yaml: field '{field}'"):
        AssessmentRunner(test_cases_dir=str(tmp_path))


@pytest.mark.parametrize("signal", ["", "   ", "\n\t"])
def test_blank_signal_is_rejected(tmp_path: Path, signal: str) -> None:
    """Reject blank leakage signals instead of matching every response."""
    _write_case(tmp_path, "blank.yaml", leakage_signal=signal)
    with pytest.raises(CaseValidationError, match="blank.yaml: field 'leakage_signal'"):
        AssessmentRunner(test_cases_dir=str(tmp_path))


def test_unknown_category_is_rejected(tmp_path: Path) -> None:
    """Reject cases whose categories are outside the supported taxonomy."""
    _write_case(tmp_path, "unknown.yaml", category="data_theft")
    with pytest.raises(CaseValidationError, match="unknown.yaml: unknown category 'data_theft'"):
        AssessmentRunner(test_cases_dir=str(tmp_path))


@pytest.mark.parametrize("case_id", ["PI-1", "pi_01", "pi_0001", "pi_001suffix"])
def test_bad_id_format_is_rejected(tmp_path: Path, case_id: str) -> None:
    """Require two lowercase letters, an underscore, and three digits."""
    _write_case(tmp_path, "bad-id.yaml", id=case_id)
    with pytest.raises(CaseValidationError, match="bad-id.yaml: id .* must look like 'pi_001'"):
        AssessmentRunner(test_cases_dir=str(tmp_path))


def test_duplicate_id_is_rejected(tmp_path: Path) -> None:
    """Reject repeated identifiers after normalizing whitespace."""
    _write_case(tmp_path, "a.yaml")
    _write_case(tmp_path, "b.yaml", id="  pi_001  ")
    with pytest.raises(CaseValidationError, match="duplicate case id 'pi_001' in b.yaml"):
        AssessmentRunner(test_cases_dir=str(tmp_path))


@pytest.mark.parametrize("contents", ["- first\n- second\n", "synthetic scalar\n", "null\n"])
def test_non_mapping_yaml_is_rejected(tmp_path: Path, contents: str) -> None:
    """Reject YAML sequences, scalars, and null documents."""
    (tmp_path / "non-mapping.yaml").write_text(contents, encoding="utf-8")
    with pytest.raises(CaseValidationError, match="non-mapping.yaml: case must be a mapping"):
        AssessmentRunner(test_cases_dir=str(tmp_path))


def test_empty_directory_is_rejected(tmp_path: Path) -> None:
    """Reject empty case sets instead of returning an empty assessment."""
    with pytest.raises(CaseValidationError, match="no test cases found"):
        AssessmentRunner(test_cases_dir=str(tmp_path))
