# PPDSA Alignment — National Strategy to Advance Privacy-Preserving Data Sharing and Analytics

**Version:** 1.0  
**Last updated:** 2026-05-17  
**Framework:** National Strategy to Advance Privacy-Preserving Data Sharing and Analytics (PPDSA), White House OSTP, March 2023  
**Modules covered:** All modules in this repository

---

## Purpose

This document maps the architecture patterns and prototype modules in this repository to
the five strategic objectives of the **National Strategy to Advance Privacy-Preserving
Data Sharing and Analytics (PPDSA)**, published by the White House Office of Science
and Technology Policy (OSTP) in March 2023.

The PPDSA identifies five key needs for advancing privacy-preserving data sharing in
the United States: (1) developing and testing privacy-preserving tools, (2) enabling
privacy-preserving research pilots, (3) promoting privacy-preserving data access methods
and repositories, (4) establishing privacy-preserving data sharing standards, and (5)
benchmarking privacy-preserving technologies.

This repository was designed in alignment with these objectives. The mapping below
documents how each module and architecture pattern contributes.

> **Reference:** White House OSTP, *National Strategy to Advance Privacy-Preserving Data
> Sharing and Analytics* (March 2023).  
> URL: <https://www.whitehouse.gov/ostp/news-updates/2023/03/14/us-releases-new-national-strategy-to-advance-privacy-preserving-data-sharing-and-analytics/>

---

## 1. Develop and Test Privacy-Preserving Tools

**PPDSA objective:** Invest in research, development, and testing of privacy-preserving
technologies such as homomorphic encryption, differential privacy, secure multi-party
computation, and synthetic data generation.

| Module / Pattern | Contribution |
|---|---|
| `fhe-feature-extraction/fhe_pipeline.py` | Implements TenSEAL CKKS homomorphic encryption for medical-image feature extraction; computes on ciphertext so raw biomedical input is never exposed during inference |
| `fhe-feature-extraction/examples/medical_image_demo.py` | End-to-end demo on a public synthetic NIfTI medical image; runnable with `python medical_image_demo.py`; validates FHE round-trip on realistic input dimensionality |
| `dp-llm-training/dp_trainer.py` | Opacus-based DP training wrapper with Gaussian noise injection and Renyi DP epsilon accounting; applies differential privacy to LLM fine-tuning |
| `dp-llm-training/examples/text_classification_demo.py` | AG News text classification demo with per-epoch (ε, δ) logging; demonstrates DP budget tracking on a public dataset |
| `dp-llm-training/budget_accountant.py` | `BudgetAccountant` class with JSON audit log and noise-multiplier search; supports pre-training budget planning and governance review |
| `llm-leakage-assessment/assessment_runner.py` | Automated LLM leakage assessment across seven threat categories; 15 YAML test cases covering prompt injection, embedding inversion, training extraction, and log capture |
| `fhe-feature-extraction/benchmarks/run_benchmark.py` | Measures encrypted-vs-cleartext feature-extraction time at three vector sizes; quantifies FHE computational overhead to support deployment tradeoff decisions |

---

## 2. Enable Privacy-Preserving Research Pilots

**PPDSA objective:** Support pilots that demonstrate privacy-preserving data sharing in
real or realistic research settings, including biomedical, clinical, and scientific
applications.

| Module / Pattern | Contribution |
|---|---|
| `architectures/biomedical-reference-architecture.md` | Paper-anchored reference architecture for clinical and population-health research; grounded in two Nature Portfolio studies that used governed cross-jurisdictional biomedical data |
| `fhe-feature-extraction/examples/medical_image_demo.py` | Simulates a privacy-preserving imaging pipeline deployable in a clinical research or biobank setting; uses a public synthetic sample (no real patient data) |
| `dp-llm-training/examples/text_classification_demo.py` | Pilot-ready DP training workflow; demonstrates the privacy budget tracking required in regulated research settings |
| Biomedical reference architecture — Layer 3 | Provides a concrete design for privacy-preserving transformation in clinical pilots: FHE-encrypted compute, DP-bounded aggregation, LLM leakage controls |
| `governance-templates/data-minimization-checklist.md` | Governance template for purpose-limitation and proportionality review — a required step in most regulated biomedical pilot agreements |

---

## 3. Promote Privacy-Preserving Data Access Methods and Repositories

**PPDSA objective:** Promote repositories, catalogs, and data-sharing platforms that
use privacy-preserving methods to expand researcher and analyst access to sensitive
datasets.

| Module / Pattern | Contribution |
|---|---|
| `architectures/biomedical-reference-architecture.md` — Layer 2 | Access-control and governance layer with DUA/IRB scope enforcement, role matrix, and audit log; foundational design for a privacy-preserving data repository |
| `governance-templates/` | Reusable templates for access-control role matrices, transformation logs, pre-export output review, and incident response — the governance artifacts that support a compliant shared repository |
| Biomedical arch — de-identification layer | Architecture-level de-identification gate before any cross-system transfer, addressing the minimum-necessary standard required for responsible data access |
| `docs/compliance/nist-control-mapping.csv` | Machine-readable control-to-pattern index enabling repository operators to verify coverage of NIST AI RMF, Privacy Framework, CSF 2.0, and HIPAA controls |
| `dashboard/` | Interactive dashboard for exploring NIST mappings, benchmark results, and leakage assessment outcomes; supports transparent communication of privacy properties to repository stakeholders |

---

## 4. Establish Privacy-Preserving Data Sharing Standards

**PPDSA objective:** Coordinate federal agency participation in developing technical
standards and interoperability specifications for privacy-preserving data sharing,
including NIST standards programs and federal data governance policies.

| Module / Pattern | Contribution |
|---|---|
| `docs/compliance/nist-control-mapping.csv` | 40-row mapping of architecture patterns to NIST AI RMF (2023), NIST Privacy Framework 1.0 (2020), and NIST CSF 2.0 (2024); uses official NIST control identifiers |
| `docs/compliance/hipaa-control-mapping.md` | Maps FHE, DP, and LLM leakage controls to HIPAA Security Rule §164.312 Technical Safeguards and §164.308 Administrative Safeguards |
| NIST SP 800-66r2 alignment (HIPAA mapping) | HIPAA mapping references NIST SP 800-66r2 (2023), the NIST guide for implementing the HIPAA Security Rule |
| Biomedical reference architecture — federal alignment table | Architecture document includes explicit alignment to NIST AI RMF GOVERN/MAP/MEASURE/MANAGE functions |
| LLM leakage threat taxonomy | Threat taxonomy categories align with NIST AI 100-1 (2023) adversarial ML taxonomy: evasion, poisoning, privacy (extraction), and abuse |

---

## 5. Benchmark Privacy-Preserving Technologies

**PPDSA objective:** Develop benchmarks and evaluation frameworks that allow researchers,
procurement officials, and deployers to compare privacy-preserving technologies across
accuracy, performance, and privacy-risk dimensions.

| Module / Pattern | Contribution |
|---|---|
| `fhe-feature-extraction/benchmarks/run_benchmark.py` | Benchmarks encrypted vs. cleartext feature extraction at 128-, 512-, and 2048-element vector sizes; reports latency, throughput, and overhead ratio |
| `fhe-feature-extraction/benchmarks/results.md` | Persistent benchmark results table; versioned alongside code so results are reproducible and comparable across library updates |
| `dp-llm-training/budget_accountant.py` | Tracks cumulative (ε, δ) across training epochs; JSON audit log enables comparison of privacy budgets across runs, models, and noise multiplier settings |
| `dp-llm-training/examples/text_classification_demo.py` | Logs per-epoch epsilon on AG News; provides a public, reproducible accuracy-vs-privacy benchmark on a standard dataset |
| `llm-leakage-assessment/assessment_runner.py` + 15 YAML cases | Defines a repeatable, machine-executable leakage assessment benchmark across seven threat categories; MockModel enables CI reproducibility |
| `docs/compliance/nist-control-mapping.csv` — `notes` column | Documents observable, testable behavior (e.g., "GaussianMechanism.compute_epsilon tracks (ε,δ) via Renyi DP composition") enabling benchmark traceability to implementation |

---

## Cross-Module Summary

| PPDSA Objective | Primary Modules | Architecture Patterns |
|---|---|---|
| 1 — Develop and test tools | `fhe-feature-extraction`, `dp-llm-training`, `llm-leakage-assessment` | FHE pipeline, DP trainer, LLM assessment runner |
| 2 — Enable pilots | `fhe-feature-extraction/examples`, `dp-llm-training/examples`, `architectures` | Biomedical reference architecture, medical-image demo, DP text-classification demo |
| 3 — Promote repositories | `architectures`, `governance-templates`, `dashboard` | Four-layer access-control design, role matrix, output-review gate, compliance dashboard |
| 4 — Establish standards | `docs/compliance`, `architectures` | NIST control mapping (CSV + MD), HIPAA mapping, federal alignment tables |
| 5 — Benchmark | `fhe-feature-extraction/benchmarks`, `dp-llm-training`, `llm-leakage-assessment` | FHE benchmark runner, budget accountant log, leakage assessment YAML cases |

---

## References

- White House OSTP, *National Strategy to Advance Privacy-Preserving Data Sharing and Analytics* (March 2023): <https://www.whitehouse.gov/ostp/news-updates/2023/03/14/us-releases-new-national-strategy-to-advance-privacy-preserving-data-sharing-and-analytics/>
- NIST AI Risk Management Framework 1.0 (2023): <https://doi.org/10.6028/NIST.AI.100-1>
- NIST Privacy Framework 1.0 (2020): <https://doi.org/10.6028/NIST.CSWP.01162020>
- NIST Cybersecurity Framework 2.0 (2024): <https://doi.org/10.6028/NIST.CSWP.29>
- NIST SP 800-66r2 — Implementing the HIPAA Security Rule (2023): <https://doi.org/10.6028/NIST.SP.800-66r2>
- See also: `docs/compliance/nist-control-mapping.csv` and `docs/compliance/hipaa-control-mapping.md`
