"""
Validate docs/compliance/nist-control-mapping.csv against expected schema and
NIST control-ID patterns.  Run standalone or via `make validate-csv`.

Exit 0 on success, 1 on any violation (suitable for CI).

Usage:
    python tools/validate_control_mapping.py
    python tools/validate_control_mapping.py --csv path/to/other.csv
    python tools/validate_control_mapping.py --min-rows 40
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Schema definition
# ---------------------------------------------------------------------------

REQUIRED_COLUMNS: set[str] = {
    "pattern",
    "module",
    "nist_ai_rmf_control",
    "nist_pf_control",
    "nist_csf_2_control",
}

# Patterns for valid NIST control IDs in each column
# AI RMF: GOVERN-1.1, MAP-2.3, MANAGE-4.2, MEASURE-1.1, etc.
_AI_RMF_RE = re.compile(r"^(GOVERN|MAP|MEASURE|MANAGE)-\d+\.\d+$", re.IGNORECASE)

# Privacy Framework: CT.PO-P1, ID.DE-P3, GV.PO-P1, PR.DS-P4, etc.
_PF_RE = re.compile(r"^(CT|ID|CM|GV|PR|RC)\.[A-Z]{2}-P\d+$", re.IGNORECASE)

# CSF 2.0: GV.OC-01, ID.AM-01, PR.DS-01, DE.AE-02, RC.RP-01, RS.MA-01, etc.
_CSF2_RE = re.compile(r"^(GV|ID|PR|DE|RS|RC)\.[A-Z]{2}-\d{2}$", re.IGNORECASE)

COLUMN_PATTERNS: dict[str, re.Pattern[str]] = {
    "nist_ai_rmf_control": _AI_RMF_RE,
    "nist_pf_control": _PF_RE,
    "nist_csf_2_control": _CSF2_RE,
}

KNOWN_MODULES: set[str] = {
    "fhe-feature-extraction",
    "dp-llm-training",
    "llm-leakage-assessment",
    "governance-templates",
    "architectures",
}

DEFAULT_CSV = Path(__file__).parent.parent / "docs" / "compliance" / "nist-control-mapping.csv"
DEFAULT_MIN_ROWS = 30


# ---------------------------------------------------------------------------
# Validation logic
# ---------------------------------------------------------------------------


@dataclass
class ValidationError:
    row: int
    column: str
    value: str
    message: str

    def __str__(self) -> str:
        return f"Row {self.row} [{self.column}={self.value!r}]: {self.message}"


@dataclass
class ValidationResult:
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    row_count: int = 0

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


def validate(csv_path: Path, min_rows: int = DEFAULT_MIN_ROWS) -> ValidationResult:
    """Validate the NIST control-mapping CSV.  Returns a ValidationResult."""
    result = ValidationResult()

    if not csv_path.exists():
        result.errors.append(ValidationError(0, "file", str(csv_path), "File not found"))
        return result

    with csv_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            result.errors.append(ValidationError(0, "header", "", "File appears empty"))
            return result

        actual_cols = set(reader.fieldnames)
        missing = REQUIRED_COLUMNS - actual_cols
        if missing:
            result.errors.append(
                ValidationError(0, "header", "", f"Missing required columns: {sorted(missing)}")
            )
            return result

        for idx, row in enumerate(reader, start=2):
            result.row_count += 1

            # Non-empty required fields
            for col in REQUIRED_COLUMNS:
                val = (row.get(col) or "").strip()
                if not val:
                    result.errors.append(ValidationError(idx, col, val, "Required field is empty"))

            # Control-ID pattern checks
            for col, pattern in COLUMN_PATTERNS.items():
                val = (row.get(col) or "").strip()
                if val and not pattern.match(val):
                    result.errors.append(
                        ValidationError(
                            idx, col, val, f"Does not match expected pattern ({pattern.pattern})"
                        )
                    )

            # Known-module check (warning, not error — new modules are expected)
            module = (row.get("module") or "").strip()
            if module and module not in KNOWN_MODULES:
                result.warnings.append(
                    f"Row {idx}: unknown module {module!r} — add to KNOWN_MODULES if intentional"
                )

    if result.row_count < min_rows:
        result.errors.append(
            ValidationError(
                0,
                "row_count",
                str(result.row_count),
                f"Expected >= {min_rows} data rows, got {result.row_count}",
            )
        )

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate the NIST control-mapping CSV schema and control-ID patterns."
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_CSV,
        metavar="PATH",
        help=f"Path to the CSV file (default: {DEFAULT_CSV})",
    )
    parser.add_argument(
        "--min-rows",
        type=int,
        default=DEFAULT_MIN_ROWS,
        metavar="N",
        help=f"Minimum number of data rows required (default: {DEFAULT_MIN_ROWS})",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress warnings; only print errors and final status",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = validate(args.csv, min_rows=args.min_rows)

    if not args.quiet:
        for warning in result.warnings:
            print(f"WARN  {warning}", file=sys.stderr)

    if result.ok:
        print(f"OK    {args.csv}: {result.row_count} rows, all checks passed.")
        return 0

    for error in result.errors:
        print(f"ERROR {error}", file=sys.stderr)
    print(
        f"FAIL  {args.csv}: {len(result.errors)} error(s) in {result.row_count} rows.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
