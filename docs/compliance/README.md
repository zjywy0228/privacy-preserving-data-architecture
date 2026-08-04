# Compliance Documentation

This folder maps the architecture patterns and prototype modules in this repository to
published NIST framework controls, HIPAA technical safeguards, and the PPDSA national
strategy objectives.

## Files

| File | Description |
|---|---|
| `nist-control-mapping.csv` | 46-row control mapping (primary reference); includes a bounded mapping of the federated FHE reference extension to the NIST Privacy Framework 1.1 Initial Public Draft |
| `nist-control-mapping.md` | Markdown summary (human-readable, fewer rows) |
| `hipaa-control-mapping.md` | HIPAA Security Rule §164.312 mapping for FHE, DP, and LLM leakage modules |
| `gdpr-article-mapping.csv` | 22-row GDPR Article 25/32/5/89 mapping for all three core workstreams |
| `ppdsa-alignment.md` | Alignment to the five PPDSA national strategy objectives (OSTP, March 2023) |

## Control mapping methodology

Each row in the CSV links one **pattern** (a specific technical mechanism or design
decision in this codebase) to:

- **NIST AI RMF control** — from the [AI Risk Management Framework (2023)](https://www.nist.gov/system/files/documents/2023/01/26/AI%20RMF%201.0.pdf). Functions: GOVERN, MAP, MEASURE, MANAGE.
- **NIST Privacy Framework control** — generally from the [Privacy Framework v1.0 (2020)](https://www.nist.gov/privacy-framework). The six federated FHE rows use identifiers from the [Privacy Framework 1.1 Initial Public Draft (April 2025)](https://www.nist.gov/privacy-framework/new-projects/privacy-framework-version-11). As checked on August 3, 2026, NIST still labels Version 1.1 an Initial Public Draft and says the final release is forthcoming; these rows must be reviewed when the final version is published.
- **NIST CSF 2.0 control** — from the [Cybersecurity Framework v2.0 (2024)](https://www.nist.gov/cyberframework). Functions: GOVERN, IDENTIFY, PROTECT, DETECT, RESPOND, RECOVER.
- **HIPAA safeguard** — section of [45 CFR Part 164](https://www.hhs.gov/hipaa/for-professionals/security/index.html) most relevant to the pattern. Biomedical data workflows often fall under HIPAA; this column assists compliance reviewers evaluating the architecture.

## How to use the CSV

Researchers and compliance reviewers can filter the CSV by:

- `module` — see all controls for a specific module (e.g., `fhe-feature-extraction`)
- `nist_ai_rmf_control` — find all patterns that implement a specific AI RMF subcategory (e.g., `MEASURE-2.5`)
- `hipaa_safeguard` — see which architecture patterns address a specific HIPAA section
- `gdpr_article` (in `gdpr-article-mapping.csv`) — find patterns that address a specific GDPR article (e.g., `Art. 25(1)`)

The NIST CSV is validated in CI (`ci.yml` `validate-nist-csv` job) to ensure column
schema and a minimum row count of 46. The job uploads a structured JSON report as
the `nist-control-mapping-validation` artifact. Generate the same report locally:

```bash
python tools/validate_control_mapping.py \
  --min-rows 46 \
  --report-json artifacts/nist-control-mapping-validation.json
```

## Limitations

This mapping reflects the **design intent** of the architecture patterns, not a formal
certification or audit finding. A qualified compliance reviewer should validate any
claims against your specific deployment context and applicable regulations.

The federated FHE rows describe only controls visible in this repository. They do not
claim that the reference coordinator supplies client authentication, transport
security, durable replay protection, or an approved institutional data-governance
process.
