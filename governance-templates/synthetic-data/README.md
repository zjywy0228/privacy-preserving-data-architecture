# Synthetic Clinical Dataset Generator

Reproducible synthetic clinical records for local testing, benchmarking,
and notebook demonstrations — with no dependency on real patient data.

## What it generates

| Column | Type | Range / Values | Source norm |
|---|---|---|---|
| `record_id` | string | `SYN-000000` … | Synthetic prefix |
| `age` | int | 18–90 | — |
| `sex` | str | M / F | — |
| `systolic_bp` | float | 80–200 mmHg | NHANES 2017-2020 |
| `diastolic_bp` | float | 50–130 mmHg | NHANES 2017-2020 |
| `glucose_mg_dl` | float | 60–400 mg/dL | NHANES fasting glucose |
| `bmi` | float | 15–60 kg/m² | NHANES adults |
| `heart_rate` | int | 40–140 bpm | Normal adult range |
| `comorbidity_count` | int | 0–5 | — |
| `on_medication` | int | 0 / 1 | — |
| `prior_hospitalization` | int | 0 / 1 | — |
| `label` | int | 0 / 1 | Configurable prevalence |

Physiological invariants enforced: `systolic_bp > diastolic_bp` always.

## Install

```bash
pip install numpy pandas
```

## Quickstart

```python
from governance_templates.synthetic_data import generate_synthetic_clinical

df = generate_synthetic_clinical(n=512, seed=42)
print(df.describe())
```

## CLI

```bash
python generate_synthetic_clinical.py --n 1000 --seed 42 --output data.csv --summary
```

```
Wrote 1000 synthetic records → data.csv
{
  "n_records": 1000,
  "n_columns": 12,
  "real_phi_used": false,
  "label_positive_rate": 0.346,
  "column_means": { "age": 53.87, "systolic_bp": 121.96, ... }
}
```

## Custom schema

```python
from governance_templates.synthetic_data import ClinicalSchemaConfig, generate_synthetic_clinical

config = ClinicalSchemaConfig(
    age_min=65,
    age_max=85,
    label_positive_rate=0.55,  # higher prevalence for elderly cohort
)
df = generate_synthetic_clinical(n=200, seed=7, config=config)
```

## With synthetic text notes

```python
df = generate_synthetic_clinical(n=100, include_text_notes=True)
print(df["clinical_note"].iloc[0])
# Patient presents for routine follow-up. BP 128.4/82.1 mmHg. BMI 31.2. No acute distress.
```

## Federal alignment

| Framework | Control | Application |
|---|---|---|
| NIST Privacy Framework | CT.PO-P3 | Data-processing policy: synthetic-only data for all testing |
| NIST AI RMF | MAP 2.1 | AI risk identification: validated test data pipeline |
| HIPAA | §164.308(a)(1) | Administrative safeguard: no real PHI in dev/test environments |
