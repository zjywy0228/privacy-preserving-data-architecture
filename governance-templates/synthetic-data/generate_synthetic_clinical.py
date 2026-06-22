"""
Synthetic Clinical Dataset Generator
======================================
Generates reproducible, statistically plausible synthetic clinical records
for local testing, benchmarking, and notebook demonstrations.

NO real patient data is used, approximated, or re-identified. All numeric
distributions are calibrated against publicly available population-level
summary statistics (e.g., CDC NHANES published tables), not individual records.

Usage:
    # As a library
    from governance_templates.synthetic_data import generate_synthetic_clinical
    df = generate_synthetic_clinical(n=512, seed=42)

    # As a CLI script
    python generate_synthetic_clinical.py --n 1000 --seed 42 --output out.csv --summary
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


@dataclass
class ClinicalSchemaConfig:
    """
    Distribution parameters for the synthetic clinical dataset.

    All defaults are based on published population norms, not real records.
    Adjust to match the distributional properties of the target study
    population when using for algorithm validation.
    """

    # Age
    age_min: int = 18
    age_max: int = 90

    # Blood pressure (mmHg) — NHANES 2017-2020 adults
    systolic_bp_mean: float = 122.0
    systolic_bp_std: float = 16.0
    systolic_bp_min: float = 80.0
    systolic_bp_max: float = 200.0

    diastolic_bp_mean: float = 78.0
    diastolic_bp_std: float = 11.0
    diastolic_bp_min: float = 50.0
    diastolic_bp_max: float = 130.0

    # Glucose (mg/dL) — fasting plasma glucose, NHANES adults
    glucose_mean: float = 104.0
    glucose_std: float = 28.0
    glucose_min: float = 60.0
    glucose_max: float = 400.0

    # BMI (kg/m²) — NHANES adults
    bmi_mean: float = 29.1
    bmi_std: float = 6.5
    bmi_min: float = 15.0
    bmi_max: float = 60.0

    # Heart rate (bpm) — resting, normal adult range
    heart_rate_mean: float = 72.0
    heart_rate_std: float = 12.0
    heart_rate_min: float = 40.0
    heart_rate_max: float = 140.0

    # Comorbidity count (0–5)
    comorbidity_max: int = 5

    # Binary label prevalence (positive class fraction)
    label_positive_rate: float = 0.35

    # Tiny per-record noise to prevent identical duplicate rows
    jitter_scale: float = 0.01


def generate_synthetic_clinical(
    n: int = 512,
    seed: int = 42,
    config: Optional[ClinicalSchemaConfig] = None,
    include_text_notes: bool = False,
) -> pd.DataFrame:
    """Generate a synthetic clinical dataset with no real PHI.

    Args:
        n: Number of records to generate.
        seed: Random seed for full reproducibility.
        config: Distribution parameters. Uses population-norm defaults if None.
        include_text_notes: When True, adds a synthetic free-text
            ``clinical_note`` column useful for NLP leakage-assessment demos.

    Returns:
        DataFrame of ``n`` synthetic clinical records. The ``record_id``
        column uses a ``SYN-XXXXXX`` prefix to make the synthetic origin
        explicit. No column contains real patient identifiers.
    """
    if config is None:
        config = ClinicalSchemaConfig()

    rng = np.random.default_rng(seed)

    # Blood pressure: enforce SBP > DBP after clipping
    sbp = rng.normal(config.systolic_bp_mean, config.systolic_bp_std, n).clip(
        config.systolic_bp_min, config.systolic_bp_max
    )
    dbp = rng.normal(config.diastolic_bp_mean, config.diastolic_bp_std, n).clip(
        config.diastolic_bp_min, config.diastolic_bp_max
    )
    dbp = np.minimum(dbp, sbp - 10.0)  # maintain physiological invariant

    glucose = rng.normal(config.glucose_mean, config.glucose_std, n).clip(
        config.glucose_min, config.glucose_max
    )
    bmi = rng.normal(config.bmi_mean, config.bmi_std, n).clip(
        config.bmi_min, config.bmi_max
    )
    hr = rng.normal(config.heart_rate_mean, config.heart_rate_std, n).clip(
        config.heart_rate_min, config.heart_rate_max
    )

    df = pd.DataFrame(
        {
            "record_id": [f"SYN-{i:06d}" for i in range(n)],
            "age": rng.integers(config.age_min, config.age_max, n),
            "sex": rng.choice(["M", "F"], n),
            "systolic_bp": np.round(sbp + rng.normal(0, config.jitter_scale, n), 1),
            "diastolic_bp": np.round(dbp + rng.normal(0, config.jitter_scale, n), 1),
            "glucose_mg_dl": np.round(glucose + rng.normal(0, config.jitter_scale, n), 1),
            "bmi": np.round(bmi + rng.normal(0, config.jitter_scale, n), 1),
            "heart_rate": np.round(hr).astype(int),
            "comorbidity_count": rng.integers(0, config.comorbidity_max + 1, n),
            "on_medication": rng.choice([0, 1], n, p=[0.55, 0.45]),
            "prior_hospitalization": rng.choice([0, 1], n, p=[0.70, 0.30]),
            "label": rng.choice(
                [0, 1],
                n,
                p=[1.0 - config.label_positive_rate, config.label_positive_rate],
            ),
        }
    )

    if include_text_notes:
        df["clinical_note"] = _generate_synthetic_notes(df, rng)

    return df


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_NOTE_TEMPLATES = [
    "Patient presents for routine follow-up. BP {sbp}/{dbp} mmHg. BMI {bmi}. No acute distress.",
    "Annual wellness visit. Fasting glucose {glu} mg/dL. HR {hr} bpm. Medications reviewed.",
    "Follow-up for {comorbidities} comorbid condition(s). Clinically stable. Continue regimen.",
    "Patient reports no new symptoms. Vitals: BP {sbp}/{dbp} mmHg, HR {hr} bpm, BMI {bmi}.",
    "Routine check. Glucose {glu} mg/dL, within acceptable range. BMI {bmi}. No changes.",
]


def _generate_synthetic_notes(df: pd.DataFrame, rng: np.random.Generator) -> list[str]:
    """Generate plausible-looking synthetic clinical note strings. No real PHI."""
    notes: list[str] = []
    template_idx = rng.integers(len(_NOTE_TEMPLATES), size=len(df))
    for i, row in enumerate(df.itertuples(index=False)):
        template = _NOTE_TEMPLATES[template_idx[i]]
        notes.append(
            template.format(
                sbp=row.systolic_bp,
                dbp=row.diastolic_bp,
                bmi=row.bmi,
                glu=row.glucose_mg_dl,
                hr=row.heart_rate,
                comorbidities=row.comorbidity_count,
            )
        )
    return notes


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a reproducible synthetic clinical dataset (no PHI).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--n", type=int, default=512, help="Number of records")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument(
        "--output",
        type=str,
        default="synthetic_clinical.csv",
        help="Output CSV path",
    )
    parser.add_argument(
        "--include-text-notes",
        action="store_true",
        help="Add a synthetic free-text clinical_note column",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a JSON summary of generated data statistics to stdout",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = _build_parser().parse_args(argv)

    df = generate_synthetic_clinical(
        n=args.n,
        seed=args.seed,
        include_text_notes=args.include_text_notes,
    )

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df)} synthetic records → {out_path}")

    if args.summary:
        numeric_cols = ["age", "systolic_bp", "diastolic_bp", "glucose_mg_dl", "bmi", "heart_rate"]
        summary = {
            "n_records": len(df),
            "n_columns": len(df.columns),
            "real_phi_used": False,
            "label_positive_rate": round(float(df["label"].mean()), 4),
            "column_means": {col: round(float(df[col].mean()), 2) for col in numeric_cols},
        }
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
