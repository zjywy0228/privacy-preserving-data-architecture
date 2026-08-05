# Privacy-Preserving Data Architecture

**中文文档:** [README.zh-CN.md](README.zh-CN.md)

[![CI](https://github.com/zjywy0228/privacy-preserving-data-architecture/actions/workflows/ci.yml/badge.svg)](https://github.com/zjywy0228/privacy-preserving-data-architecture/actions/workflows/ci.yml)
[![Publish to TestPyPI](https://github.com/zjywy0228/privacy-preserving-data-architecture/actions/workflows/publish-testpypi.yml/badge.svg)](https://github.com/zjywy0228/privacy-preserving-data-architecture/actions/workflows/publish-testpypi.yml)
[![GitHub Release](https://img.shields.io/github/v/release/zjywy0228/privacy-preserving-data-architecture)](https://github.com/zjywy0228/privacy-preserving-data-architecture/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Last commit](https://img.shields.io/github/last-commit/zjywy0228/privacy-preserving-data-architecture)](https://github.com/zjywy0228/privacy-preserving-data-architecture/commits/master)

> **What's new (2026-08-04):** [`v0.4.1`](https://github.com/zjywy0228/privacy-preserving-data-architecture/releases/tag/v0.4.1) corrects and regression-tests the biomedical citation record and publishes a dated twelve-month technical roadmap. [Full changelog →](CHANGELOG.md)

Reusable architecture patterns, prototype modules, and assessment frameworks for institutions that need to analyze sensitive biomedical and scientific data while controlling raw-data exposure, AI leakage risk, and compliance obligations.

Maintained by Junyi Zhang ([@zjywy0228](https://github.com/zjywy0228)). Issues and feedback welcome.

**[→ Live project dashboard](https://zjywy0228.github.io/privacy-preserving-data-architecture/)** — module status, NIST control mappings, leakage assessment results, FHE benchmark timings, and live commit feed.

[![Dashboard preview](docs/assets/img/dashboard-preview.png)](https://zjywy0228.github.io/privacy-preserving-data-architecture/)

## Motivation

Modern biomedical and scientific research increasingly depends on cross-institutional data collaboration. Two recurring constraints make that collaboration difficult:

1. **Regulatory and ethical limits on raw-data movement.** Patient records, pediatric clinical data, health registry data, genomic data, and equivalent scientific datasets are subject to HIPAA, GDPR Article 9, Sweden's *Patientdatalag*, and related frameworks that restrict how raw records can be shared, copied, or moved across systems and jurisdictions.

2. **AI-era data-leakage risk.** AI and large language model (LLM) systems trained on or given access to sensitive data can expose that data through memorization, membership inference, prompt injection, log capture, and downstream tool leakage — risks that conventional access-control architectures were not designed for.

This repository translates research on **fully homomorphic encryption (FHE)**, **differential privacy (DP)**, and **LLM data-leakage assessment** into practical architecture patterns and prototype modules that research teams, hospital IT groups, and compliance reviewers can evaluate and adapt.

## Research Foundation

This work builds on the following published research:

| Paper | Venue | DOI / Link |
|---|---|---|
| *Privacy-Preserving Feature Extraction for Medical Images Based on Fully Homomorphic Encryption* | Journal of Advanced Computing Systems, 4(2), 15–28 (2024) | [doi:10.69987/JACS.2024.40202](https://doi.org/10.69987/JACS.2024.40202) |
| *A Differential Privacy-Based Mechanism for Preventing Data Leakage in Large Language Model Training* | Academic Journal of Sociology and Management, 3(2), 33–42 (2025) | [doi:10.70393/616a736d.323732](https://doi.org/10.70393/616a736d.323732) |
| *Assessment Methods and Protection Strategies for Data Leakage Risks in Large Language Models* | Journal of Industrial Engineering and Applied Science, 3(2), 6–15 (2025) | [doi:10.70393/6a69656173.323736](https://doi.org/10.70393/6a69656173.323736) |
| *Hospital-treated infectious diseases and the risk of epilepsy in older age* | Nature Aging, 5, 2188–2196 (2025) | [doi:10.1038/s43587-025-01005-x](https://doi.org/10.1038/s43587-025-01005-x) |
| *Growth and sleep outcomes after adenotonsillectomy in pediatric mild sleep-disordered breathing* | Scientific Reports, 16, Article 688 (2026) | [doi:10.1038/s41598-025-30271-3](https://doi.org/10.1038/s41598-025-30271-3) |

The Nature Aging and Scientific Reports biomedical papers are cited only as
application-domain context for governed sensitive-data research. This repository
does not infer any individual author's responsibilities beyond each paper's
published contribution statement.

Threat assumptions and residual risks are documented in
[`docs/threat-models/`](docs/threat-models/README.md).

## Repository Structure

```
privacy-preserving-data-architecture/
├── architectures/                # Reference architectures (institution-agnostic, paper-anchored)
│   ├── README.md                 # pattern index
│   └── biomedical-reference-architecture.md  # four-layer clinical/registry governed-data design
├── fhe-feature-extraction/       # FHE pipeline for encrypted medical-image features
│   ├── fhe_pipeline.py
│   └── examples/
├── dp-llm-training/              # Differential privacy wrapper for LLM/ML training
│   ├── dp_trainer.py
│   └── examples/
├── llm-leakage-assessment/       # LLM data-leakage threat taxonomy and checklist
│   ├── ASSESSMENT-CHECKLIST.md
│   └── threat-taxonomy.md
├── governance-templates/         # Data minimization template
│   └── data-minimization-checklist.md
└── docs/compliance/
    └── nist-control-mapping.md
```

## Quick Start

### FHE Feature Extraction

```bash
pip install tenseal numpy Pillow scikit-learn
python fhe-feature-extraction/examples/basic_usage.py
```

### Differential Privacy Training

```bash
pip install opacus torch transformers
python dp-llm-training/examples/demo_training.py
```

### LLM Leakage Assessment

Review `llm-leakage-assessment/ASSESSMENT-CHECKLIST.md` for the structured workflow. The Python runner (`assessment_runner.py`) automates the prompt-injection and log-capture test cases.

## Deliverable Roadmap

| Phase | Target | Status |
|---|---|---|
| Phase 1 | Initial FHE prototype, DP wrapper, LLM leakage checklist | Complete |
| Phase 1.2 | Biomedical reference architecture — four-layer design anchored to Nature Aging + Scientific Reports papers | **Live** (2026-05-12) |
| Phase 2 | Citation-integrity maintenance and dated governance-template improvements | `v0.4.1` released; `v0.5.0` target 2026-11-30 |
| Phase 3 | Artifact-specific feedback and expanded reproducible validation | `v0.6.0` target 2027-02-28; `v0.7.0` target 2027-05-31 |
| Phase 4 | Public dissemination and twelve-month maintenance report | Target 2027-08-03 |

See [`ROADMAP.md`](ROADMAP.md) for release criteria, feedback boundaries, and
the complete twelve-month plan.

## Target Users

- **Biomedical research teams** setting up cross-institutional studies on patient-level data
- **Hospital IT and compliance groups** evaluating AI tools for clinical data environments
- **Scientific collaboration teams** managing access to sensitive simulation, calibration, or pre-publication research data
- **Data engineers and security architects** building privacy-conscious ML pipelines on regulated data

## Federal Policy Alignment

This work is designed to be compatible with:

- [NIST Privacy Framework](https://www.nist.gov/privacy-framework)
- [NIST AI Risk Management Framework (AI RMF)](https://www.nist.gov/system/files/documents/2023/01/26/AI%20RMF%201.0.pdf)
- [NIST Adversarial ML Report (2025)](https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-2e2025.pdf)
- [CISA AI Data Security Best Practices](https://www.cisa.gov/resources-tools/resources/guidelines-secure-ai-system-development)
- [HHS OCR HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/index.html)
- [National Strategy to Advance Privacy-Preserving Data Sharing and Analytics (PPDSA)](https://www.whitehouse.gov/wp-content/uploads/2023/03/National-Strategy-to-Advance-Privacy-Preserving-Data-Sharing-and-Analytics.pdf)

## Citation

If you use materials from this repository in your research, please cite the relevant papers above.

## License

MIT License. See [LICENSE](LICENSE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to contribute code, documentation, and architecture patterns.

---

## AI-Assistance Disclosure

Some commits in this repository were prepared with AI coding assistance (Claude). All AI-generated code has been reviewed and tested by the maintainer before merge. The architectural decisions, threat models, and design choices reflect the maintainer's own research direction.

The use of AI coding assistance is itself within the scope of this repository's `llm-leakage-assessment/` module — see [`docs/ai-assistance-policy.md`](docs/ai-assistance-policy.md) for how AI-assisted contributions are reviewed, tested, and disclosed.

---

*This is an active research project; architecture patterns and prototype implementations will evolve. Interfaces may change between minor versions.*
