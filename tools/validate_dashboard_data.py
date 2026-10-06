"""Validate the JSON files the static dashboard publishes."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BENCHMARK_MODES = {"measured", "archived_record"}
LEAKAGE_MODES = {"measured", "synthetic_fixture", "mock", "illustrative_sample"}
MODES_REQUIRING_COMMIT = {"measured", "synthetic_fixture", "mock"}
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{7,40}$")


def _is_number(value: object) -> bool:
    """Return True when value is a finite int or float (but not bool)."""
    if isinstance(value, bool):
        return False
    if not isinstance(value, (int, float)):
        return False
    return math.isfinite(value)


def _is_count(value: object, minimum: int) -> bool:
    """Return True when value is a non-bool int at least `minimum`."""
    if isinstance(value, bool):
        return False
    if not isinstance(value, int):
        return False
    return value >= minimum


def validate_provenance(provenance: object, allowed: set[str], label: str) -> list[str]:
    """Validate the provenance block of a dashboard-data file."""
    if not isinstance(provenance, dict):
        return [f"{label}.provenance: object is required"]
    mode = provenance.get("run_mode")
    if mode not in allowed:
        return [f"{label}.provenance.run_mode: expected one of {sorted(allowed)}, got {mode!r}"]
    errors: list[str] = []
    if mode in MODES_REQUIRING_COMMIT:
        source_commit = provenance.get("source_commit")
        if not isinstance(source_commit, str) or not COMMIT_PATTERN.match(source_commit):
            errors.append(
                f"{label}.provenance.source_commit: expected a 7-40 char hex commit, "
                f"got {source_commit!r}"
            )
        generated_at = provenance.get("generated_at")
        if not isinstance(generated_at, str):
            errors.append(
                f"{label}.provenance.generated_at: expected an ISO timestamp string, "
                f"got {generated_at!r}"
            )
        else:
            try:
                datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
            except ValueError:
                errors.append(
                    f"{label}.provenance.generated_at: cannot parse {generated_at!r} "
                    "as ISO timestamp"
                )
        generator = provenance.get("generator")
        if not isinstance(generator, str) or not generator.strip():
            errors.append(
                f"{label}.provenance.generator: expected a non-empty string, got {generator!r}"
            )
    else:
        source = provenance.get("source")
        if not isinstance(source, str) or not source.strip():
            errors.append(f"{label}.provenance.source: expected a non-empty string, got {source!r}")
        note = provenance.get("note")
        if not isinstance(note, str) or not note.strip():
            errors.append(f"{label}.provenance.note: expected a non-empty string, got {note!r}")
    return errors


def validate_benchmark(data: object) -> list[str]:
    """Validate a parsed benchmark.json object."""
    label = "benchmark"
    if not isinstance(data, dict):
        return [f"{label}: object is required"]
    errors: list[str] = []
    errors.extend(validate_provenance(data.get("provenance"), BENCHMARK_MODES, label))
    scheme = data.get("scheme")
    if not isinstance(scheme, str) or not scheme.strip():
        errors.append(f"{label}.scheme: expected a non-empty string, got {scheme!r}")
    rows = data.get("rows")
    if not isinstance(rows, list) or not rows:
        errors.append(f"{label}.rows: expected a non-empty list, got {rows!r}")
    else:
        previous_size: int | None = None
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                errors.append(f"{label}.rows[{index}]: object is required")
                continue
            vector_size = row.get("vector_size")
            if not _is_count(vector_size, 1) or (
                previous_size is not None and vector_size <= previous_size
            ):
                errors.append(
                    f"{label}.rows[{index}].vector_size: expected a positive integer "
                    f"greater than the previous row, got {vector_size!r}"
                )
            else:
                previous_size = int(vector_size)
            cleartext_ms = row.get("cleartext_ms")
            if not _is_number(cleartext_ms) or cleartext_ms <= 0:
                errors.append(
                    f"{label}.rows[{index}].cleartext_ms: expected a positive finite number, "
                    f"got {cleartext_ms!r}"
                )
            ciphertext_ms = row.get("ciphertext_ms")
            if not _is_number(ciphertext_ms) or ciphertext_ms <= 0:
                errors.append(
                    f"{label}.rows[{index}].ciphertext_ms: expected a positive finite number, "
                    f"got {ciphertext_ms!r}"
                )
    provenance = data.get("provenance") if isinstance(data.get("provenance"), dict) else {}
    if isinstance(provenance, dict) and provenance.get("run_mode") == "measured":
        trials = data.get("trials")
        if not _is_count(trials, 3):
            errors.append(f"{label}.trials: expected an integer of at least 3, got {trials!r}")
        statistic = data.get("statistic")
        if statistic != "median":
            errors.append(f"{label}.statistic: expected 'median', got {statistic!r}")
        platform_value = data.get("platform")
        if not isinstance(platform_value, str) or not platform_value.strip():
            errors.append(f"{label}.platform: expected a non-empty string, got {platform_value!r}")
    return errors


def validate_leakage(data: object) -> list[str]:
    """Validate a parsed leakage-results.json object."""
    label = "leakage"
    if not isinstance(data, dict):
        return [f"{label}: object is required"]
    errors: list[str] = []
    errors.extend(validate_provenance(data.get("provenance"), LEAKAGE_MODES, label))
    provenance = data.get("provenance") if isinstance(data.get("provenance"), dict) else {}
    mode = provenance.get("run_mode") if isinstance(provenance, dict) else None
    if mode in MODES_REQUIRING_COMMIT:
        model_id = data.get("model_id")
        if not isinstance(model_id, str) or not model_id.strip():
            errors.append(
                f"{label}.model_id: expected a non-empty string for run_mode {mode!r}, "
                f"got {model_id!r}"
            )
    categories = data.get("categories")
    if not isinstance(categories, list) or not categories:
        errors.append(f"{label}.categories: expected a non-empty list, got {categories!r}")
    else:
        seen_names: set[str] = set()
        for index, category in enumerate(categories):
            if not isinstance(category, dict):
                errors.append(f"{label}.categories[{index}]: object is required")
                continue
            name = category.get("name")
            if not isinstance(name, str) or not name.strip():
                errors.append(
                    f"{label}.categories[{index}].name: expected a non-empty string, got {name!r}"
                )
            elif name in seen_names:
                errors.append(f"{label}.categories[{index}].name: duplicate category name {name!r}")
            else:
                seen_names.add(name)
            passed = category.get("passed")
            total = category.get("total")
            if not _is_count(passed, 0):
                errors.append(
                    f"{label}.categories[{index}].passed: expected an integer >= 0, got {passed!r}"
                )
            if not _is_count(total, 1):
                errors.append(
                    f"{label}.categories[{index}].total: expected an integer >= 1, got {total!r}"
                )
            if (
                _is_count(passed, 0) and _is_count(total, 1) and passed > total  # type: ignore[operator]
            ):
                errors.append(
                    f"{label}.categories[{index}]: passed ({passed}) cannot exceed total ({total})"
                )
    return errors


def validate_directory(data_dir: Path) -> list[str]:
    """Validate every published dashboard-data file in `data_dir`."""
    validators: list[tuple[str, Callable[[object], list[str]]]] = [
        ("benchmark.json", validate_benchmark),
        ("leakage-results.json", validate_leakage),
    ]
    errors: list[str] = []
    for name, validator in validators:
        path = data_dir / name
        if not path.exists():
            errors.append(f"{name}: file not found")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{name}: invalid JSON ({exc})")
            continue
        for error in validator(data):
            errors.append(f"{name}: {error}")
    return errors


def main(argv: list[str] | None = None) -> int:
    """Entry point for the dashboard-data validator CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=REPO_ROOT / "docs" / "assets" / "data",
    )
    parser.add_argument("--report-json", type=Path, default=None)
    args = parser.parse_args(argv)

    errors = validate_directory(args.data_dir)

    if args.report_json is not None:
        args.report_json.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "schema_version": "1.0",
            "status": "pass" if not errors else "fail",
            "errors": errors,
        }
        args.report_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if errors:
        for message in errors:
            print(f"ERROR {message}")
        return 1
    print("[PASS] dashboard data is valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
