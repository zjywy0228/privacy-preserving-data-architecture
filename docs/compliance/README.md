# Compliance Documentation

This folder maps the architecture patterns and prototype modules in this repository to
published NIST framework controls and HIPAA technical safeguards.

## Files

| File | Description |
|---|---|
| `nist-control-mapping.csv` | 40-row control mapping (primary reference) |
| `nist-control-mapping.md` | Markdown summary (human-readable, fewer rows) |

## Control mapping methodology

Each row in the CSV links one **pattern** (a specific technical mechanism or design
decision in this codebase) to:

- **NIST AI RMF control** — from the [AI Risk Management Framework (2023)](https://www.nist.gov/system/files/documents/2023/01/26/AI%20RMF%201.0.pdf). Functions: GOVERN, MAP, MEASURE, MANAGE.
- **NIST Privacy Framework control** — from the [Privacy Framework v1.0 (2020)](https://www.nist.gov/privacy-framework). Functions: IDENTIFY, GOVERN, CONTROL, COMMUNICATE, PROTECT.
- **NIST CSF 2.0 control** — from the [Cybersecurity Framework v2.0 (2024)](https://www.nist.gov/cyberframework). Functions: GOVERN, IDENTIFY, PROTECT, DETECT, RESPOND, RECOVER.
- **HIPAA safeguard** — section of [45 CFR Part 164](https://www.hhs.gov/hipaa/for-professionals/security/index.html) most relevant to the pattern. Biomedical data workflows often fall under HIPAA; this column assists compliance reviewers evaluating the architecture.

## How to use the CSV

Researchers and compliance reviewers can filter the CSV by:

- `module` — see all controls for a specific module (e.g., `fhe-feature-extraction`)
- `nist_ai_rmf_control` — find all patterns that implement a specific AI RMF subcategory (e.g., `MEASURE-2.5`)
- `hipaa_safeguard` — see which architecture patterns address a specific HIPAA section

The CSV is validated in CI (`ci.yml` `validate-nist-csv` job) to ensure column
schema and a minimum row count of 30.

## Limitations

This mapping reflects the **design intent** of the architecture patterns, not a formal
certification or audit finding. A qualified compliance reviewer should validate any
claims against your specific deployment context and applicable regulations.
