"""Unit tests for the synthetic clinical dataset generator."""

from __future__ import annotations

import os
import sys

import pandas as pd

# governance-templates/synthetic-data uses hyphens (invalid package identifiers),
# so we add its path directly instead of using a dotted import.
_SYNTH_DIR = os.path.join(os.path.dirname(__file__), "..", "governance-templates", "synthetic-data")
sys.path.insert(0, os.path.abspath(_SYNTH_DIR))

from generate_synthetic_clinical import (  # noqa: E402
    ClinicalSchemaConfig,
    generate_synthetic_clinical,
)

# ---------------------------------------------------------------------------
# Shape and schema
# ---------------------------------------------------------------------------


def test_default_output_shape() -> None:
    df = generate_synthetic_clinical(n=100, seed=0)
    assert df.shape[0] == 100
    assert df.shape[1] == 12  # 11 clinical columns + label


def test_column_names() -> None:
    df = generate_synthetic_clinical(n=10, seed=0)
    expected = {
        "record_id",
        "age",
        "sex",
        "systolic_bp",
        "diastolic_bp",
        "glucose_mg_dl",
        "bmi",
        "heart_rate",
        "comorbidity_count",
        "on_medication",
        "prior_hospitalization",
        "label",
    }
    assert set(df.columns) == expected


def test_record_id_prefix() -> None:
    df = generate_synthetic_clinical(n=5, seed=0)
    assert all(rid.startswith("SYN-") for rid in df["record_id"])


# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------


def test_same_seed_is_reproducible() -> None:
    df1 = generate_synthetic_clinical(n=50, seed=7)
    df2 = generate_synthetic_clinical(n=50, seed=7)
    pd.testing.assert_frame_equal(df1, df2)


def test_different_seeds_differ() -> None:
    df1 = generate_synthetic_clinical(n=50, seed=1)
    df2 = generate_synthetic_clinical(n=50, seed=2)
    # At least one numeric column must differ
    assert not df1["glucose_mg_dl"].equals(df2["glucose_mg_dl"])


# ---------------------------------------------------------------------------
# Physiological invariants
# ---------------------------------------------------------------------------


def test_systolic_always_greater_than_diastolic() -> None:
    df = generate_synthetic_clinical(n=512, seed=42)
    assert (df["systolic_bp"] > df["diastolic_bp"]).all(), (
        "Physiological invariant violated: some SBP ≤ DBP"
    )


def test_value_ranges() -> None:
    df = generate_synthetic_clinical(n=512, seed=42)
    assert df["age"].between(18, 90).all()
    assert df["systolic_bp"].between(80, 200).all()
    assert df["diastolic_bp"].between(50, 130).all()
    assert df["glucose_mg_dl"].between(60, 400).all()
    assert df["bmi"].between(15, 60).all()
    assert df["heart_rate"].between(40, 140).all()
    assert df["comorbidity_count"].between(0, 5).all()
    assert set(df["on_medication"].unique()).issubset({0, 1})
    assert set(df["prior_hospitalization"].unique()).issubset({0, 1})


def test_label_is_binary() -> None:
    df = generate_synthetic_clinical(n=200, seed=42)
    assert set(df["label"].unique()).issubset({0, 1})


def test_sex_values() -> None:
    df = generate_synthetic_clinical(n=200, seed=42)
    assert set(df["sex"].unique()).issubset({"M", "F"})


# ---------------------------------------------------------------------------
# Uniqueness (jitter prevents exact duplicates)
# ---------------------------------------------------------------------------


def test_no_exact_numeric_duplicates() -> None:
    numeric_cols = ["systolic_bp", "diastolic_bp", "glucose_mg_dl", "bmi"]
    df = generate_synthetic_clinical(n=200, seed=42)
    assert df[numeric_cols].duplicated().sum() == 0


# ---------------------------------------------------------------------------
# Custom config
# ---------------------------------------------------------------------------


def test_custom_age_range() -> None:
    config = ClinicalSchemaConfig(age_min=65, age_max=80)
    df = generate_synthetic_clinical(n=300, seed=99, config=config)
    assert df["age"].between(65, 80).all()


def test_custom_label_prevalence() -> None:
    config = ClinicalSchemaConfig(label_positive_rate=0.8)
    df = generate_synthetic_clinical(n=500, seed=99, config=config)
    # With n=500 and rate=0.8, observed rate should be close (±0.1)
    observed = df["label"].mean()
    assert 0.70 <= observed <= 0.90, f"Label prevalence {observed:.2f} far from target 0.80"


# ---------------------------------------------------------------------------
# Text notes
# ---------------------------------------------------------------------------


def test_text_notes_column_present() -> None:
    df = generate_synthetic_clinical(n=20, seed=0, include_text_notes=True)
    assert "clinical_note" in df.columns
    assert df["clinical_note"].notna().all()


def test_text_notes_not_in_default() -> None:
    df = generate_synthetic_clinical(n=20, seed=0, include_text_notes=False)
    assert "clinical_note" not in df.columns


def test_text_notes_no_record_ids() -> None:
    """Clinical notes must not contain synthetic record IDs (privacy hygiene)."""
    df = generate_synthetic_clinical(n=30, seed=0, include_text_notes=True)
    for note in df["clinical_note"]:
        assert "SYN-" not in note
