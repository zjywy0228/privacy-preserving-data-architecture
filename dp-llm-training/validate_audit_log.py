"""
Validator for DP training audit logs produced by budget_accountant.py.

WHY THIS EXISTS:
    BudgetAccountant.save_log() writes a JSON audit file that governance
    reviewers can attach to a model card or submit to a compliance audit.
    This validator confirms the file is structurally correct and internally
    consistent before it is shared externally -- catching truncated runs,
    corrupted files, or budget overruns that were not caught at training time.

    Run standalone (CLI) or import validate_log() for use in CI pipelines.

Usage
-----
    python dp-llm-training/validate_audit_log.py path/to/audit.json
    python dp-llm-training/validate_audit_log.py path/to/audit.json --strict
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Validation result
# ---------------------------------------------------------------------------


@dataclass
class ValidationResult:
    """Structured outcome of a single audit-log validation run."""

    path: str
    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        lines = [f"[{status}] {self.path}"]
        for e in self.errors:
            lines.append(f"  ERROR   {e}")
        for w in self.warnings:
            lines.append(f"  WARNING {w}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core validation logic
# ---------------------------------------------------------------------------


def validate_log(path: str | Path, *, strict: bool = False) -> ValidationResult:
    """Validate a DP audit-log JSON file produced by BudgetAccountant.save_log().

    Checks
    ------
    Structural
        File is valid JSON; top-level ``metadata`` and ``log`` keys present;
        ``metadata`` fields have correct types and positive values; ``log``
        is a non-empty list of epoch records with all required keys.

    Logical (always enforced)
        Epochs strictly ascending; ``cumulative_steps`` non-decreasing;
        ``epsilon_spent`` non-decreasing; ``budget_fraction`` consistent with
        ``epsilon_spent / target_epsilon``; ``budget_exhausted`` agrees with
        ``epsilon_spent >= target_epsilon``; per-record ``delta`` matches
        ``metadata.target_delta``.

    Strict mode
        Promotes advisory range warnings (epsilon > 10, noise_multiplier < 0.5,
        sample_rate > 0.1) to errors. Use for CI gates on new training runs.
    """
    path = Path(path)
    result = ValidationResult(path=str(path), passed=True)

    # 1. Read and parse
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        result.errors.append(f"Cannot read file: {exc}")
        result.passed = False
        return result

    try:
        data: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError as exc:
        result.errors.append(f"Invalid JSON: {exc}")
        result.passed = False
        return result

    if not isinstance(data, dict):
        result.errors.append("Root must be a JSON object.")
        result.passed = False
        return result

    # 2. Top-level keys
    for key in ("metadata", "log"):
        if key not in data:
            result.errors.append(f"Missing required top-level key: {key!r}.")
    if result.errors:
        result.passed = False
        return result

    # 3. Metadata
    meta = data["metadata"]
    if not isinstance(meta, dict):
        result.errors.append("metadata must be a JSON object.")
        result.passed = False
        return result

    def _require_positive_number(obj: dict[str, Any], key: str, label: str) -> float | None:
        if key not in obj:
            result.errors.append(f"{label}: missing required field {key!r}.")
            return None
        val = obj[key]
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            result.errors.append(f"{label}.{key}: expected a number, got {type(val).__name__}.")
            return None
        if val <= 0:
            result.errors.append(f"{label}.{key}: must be > 0, got {val}.")
            return None
        return float(val)

    target_epsilon = _require_positive_number(meta, "target_epsilon", "metadata")
    target_delta = _require_positive_number(meta, "target_delta", "metadata")
    noise_multiplier = _require_positive_number(meta, "noise_multiplier", "metadata")
    sample_rate = _require_positive_number(meta, "sample_rate", "metadata")

    if target_delta is not None and target_delta >= 1.0:
        result.errors.append(f"metadata.target_delta must be < 1, got {target_delta}.")
        target_delta = None
    if sample_rate is not None and sample_rate > 1.0:
        result.errors.append(f"metadata.sample_rate must be <= 1, got {sample_rate}.")
        sample_rate = None

    # Advisory range checks
    _advisory = result.errors if strict else result.warnings
    if target_epsilon is not None and target_epsilon > 10.0:
        _advisory.append(
            f"metadata.target_epsilon={target_epsilon} is large (>10); privacy guarantee may be weak."
        )
    if noise_multiplier is not None and noise_multiplier < 0.5:
        _advisory.append(
            f"metadata.noise_multiplier={noise_multiplier} is small (<0.5); epsilon may grow quickly."
        )
    if sample_rate is not None and sample_rate > 0.1:
        _advisory.append(
            f"metadata.sample_rate={sample_rate} is high (>0.1); privacy amplification benefit is reduced."
        )

    # 4. Log array
    log = data["log"]
    if not isinstance(log, list):
        result.errors.append("log must be a JSON array.")
        result.passed = False
        return result
    if len(log) == 0:
        result.errors.append("log must contain at least one epoch record.")
        result.passed = False
        return result

    required_keys = {
        "epoch",
        "cumulative_steps",
        "epsilon_spent",
        "delta",
        "loss",
        "budget_fraction",
        "budget_exhausted",
    }

    prev_epoch = 0
    prev_steps = 0
    prev_epsilon = -1.0

    for i, record in enumerate(log):
        loc = f"log[{i}]"
        if not isinstance(record, dict):
            result.errors.append(f"{loc}: each record must be a JSON object.")
            continue

        missing = required_keys - record.keys()
        if missing:
            result.errors.append(f"{loc}: missing required fields: {sorted(missing)}.")
            continue

        # Type extraction helpers
        epoch_v = record["epoch"]
        steps_v = record["cumulative_steps"]
        eps_v = record["epsilon_spent"]
        delta_v = record["delta"]
        loss_v = record["loss"]
        bf_v = record["budget_fraction"]
        be_v = record["budget_exhausted"]

        if isinstance(epoch_v, bool) or not isinstance(epoch_v, int) or epoch_v < 1:
            result.errors.append(f"{loc}.epoch: positive integer required, got {epoch_v!r}.")
            epoch_v = None
        if isinstance(steps_v, bool) or not isinstance(steps_v, int) or steps_v < 1:
            result.errors.append(
                f"{loc}.cumulative_steps: positive integer required, got {steps_v!r}."
            )
            steps_v = None
        if isinstance(eps_v, bool) or not isinstance(eps_v, (int, float)) or eps_v < 0:
            result.errors.append(
                f"{loc}.epsilon_spent: non-negative number required, got {eps_v!r}."
            )
            eps_v = None
        if isinstance(delta_v, bool) or not isinstance(delta_v, (int, float)):
            result.errors.append(f"{loc}.delta: number required.")
            delta_v = None
        if isinstance(loss_v, bool) or not isinstance(loss_v, (int, float)) or loss_v < 0:
            result.errors.append(f"{loc}.loss: non-negative number required, got {loss_v!r}.")
        if (
            isinstance(bf_v, bool)
            or not isinstance(bf_v, (int, float))
            or not (0.0 <= float(bf_v) <= 1.0)
        ):
            result.errors.append(f"{loc}.budget_fraction: number in [0,1] required, got {bf_v!r}.")
            bf_v = None
        if not isinstance(be_v, bool):
            result.errors.append(f"{loc}.budget_exhausted: boolean required, got {be_v!r}.")
            be_v = None

        # Monotonicity
        if epoch_v is not None:
            if epoch_v <= prev_epoch:
                result.errors.append(
                    f"{loc}.epoch: must increase monotonically; got {epoch_v} after {prev_epoch}."
                )
            else:
                prev_epoch = epoch_v
        if steps_v is not None:
            if steps_v < prev_steps:
                result.errors.append(
                    f"{loc}.cumulative_steps: must be non-decreasing; got {steps_v} after {prev_steps}."
                )
            else:
                prev_steps = steps_v
        if eps_v is not None:
            if eps_v < prev_epsilon - 1e-9:
                result.errors.append(
                    f"{loc}.epsilon_spent: must be non-decreasing; got {eps_v} after {prev_epsilon:.6f}."
                )
            else:
                prev_epsilon = eps_v

        # budget_fraction consistency
        if eps_v is not None and bf_v is not None and target_epsilon is not None:
            expected = min(eps_v / target_epsilon, 1.0)
            if abs(float(bf_v) - expected) > 1e-4:
                result.errors.append(
                    f"{loc}.budget_fraction: expected ~{expected:.6f} "
                    f"(epsilon_spent/target_epsilon), got {bf_v}."
                )

        # budget_exhausted consistency
        if eps_v is not None and be_v is not None and target_epsilon is not None:
            expected_be = eps_v >= target_epsilon
            if be_v != expected_be:
                result.errors.append(
                    f"{loc}.budget_exhausted: expected {expected_be} "
                    f"(epsilon_spent={eps_v} vs target={target_epsilon}), got {be_v}."
                )

        # delta matches metadata
        if delta_v is not None and target_delta is not None:
            if abs(delta_v - target_delta) > 1e-15:
                result.warnings.append(
                    f"{loc}.delta={delta_v} differs from metadata.target_delta={target_delta}."
                )

    result.passed = len(result.errors) == 0
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="validate_audit_log",
        description=(
            "Validate a DP training audit-log JSON file produced by "
            "dp-llm-training/budget_accountant.py. "
            "Exits 0 on pass, 1 on failure."
        ),
    )
    p.add_argument("path", help="Path to the audit-log JSON file.")
    p.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Promote advisory range warnings to errors.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = validate_log(args.path, strict=args.strict)
    print(result)
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
