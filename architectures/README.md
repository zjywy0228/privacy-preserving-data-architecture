# Architecture Patterns

Reference architectures for privacy-preserving, AI-resilient data analysis in regulated biomedical and scientific research settings.

Each pattern documents a repeatable, institution-agnostic design that can be evaluated, adapted, and validated by research teams, hospital IT groups, compliance reviewers, and security architects without needing access to the original protected datasets.

---

## Patterns in This Directory

| File | Coverage | Anchored Papers |
|---|---|---|
| [`biomedical-reference-architecture.md`](biomedical-reference-architecture.md) | Four-layer reference architecture for clinical and population-health governed-data workflows | Nature Aging (2025) — epilepsy/infectious disease; Scientific Reports (2025) — pediatric sleep-disordered breathing |

---

## Planned Patterns

- **Scientific Governed-Access Pattern** — controlled data-release architecture for large-scale scientific collaborations (petabyte-scale, multi-institution, pre-publication embargo); maps to `scientific-governed-access/` module (Day 5 milestone)
- **LLM-Augmented Analytics Pattern** — governed workflow for deploying LLM tooling on regulated personal data; maps to `llm-leakage-assessment/` and `dp-llm-training/` modules (Day 4 milestone)
- **Cross-Jurisdictional Research Pattern** — architecture for studies that span HIPAA (US), GDPR/Patientdatalag (EU/Sweden), and China PIPL environments

---

## How Architecture Patterns Relate to Prototype Modules

Each pattern in this directory specifies *what controls to apply* at each workflow layer. The prototype modules in the repository root provide *working implementations* of the core privacy mechanisms:

| Control mechanism | Repository module |
|---|---|
| Encrypted computation (FHE/CKKS) | `fhe-feature-extraction/` |
| Privacy-bounded model training (DP) | `dp-llm-training/` |
| LLM data-leakage assessment | `llm-leakage-assessment/` |
| Data minimization and access governance | `governance-templates/` |
| Compliance mapping (NIST, HIPAA, PPDSA) | `docs/compliance/` |

Architecture patterns reference these modules by name so that a team can adopt a pattern and then drop in the corresponding prototype module for the relevant control layer.
