# Biomedical Reference Architecture

## Privacy-Preserving Governed-Data Workflows for Clinical and Population-Health Research

**Version:** 1.0  
**Last updated:** 2026-05-12  
**Status:** Initial release — public review

---

## 1. Purpose and Scope

This reference architecture documents a repeatable four-layer design for biomedical research teams that must analyze sensitive patient records — including clinical trial data, population-health registry data, and multi-jurisdictional health datasets — while maintaining controlled access, data minimization, and compliance with HIPAA, EU GDPR Article 9, Sweden's *Patientdatalag*, and equivalent frameworks.

The architecture is **paper-anchored**: each layer is grounded in the data-governance constraints documented in two peer-reviewed Nature Portfolio biomedical studies that informed its design:

- **Nature Aging (2025):** *Hospital-treated infectious diseases and the risk of epilepsy in older age* — used UK Biobank and Swedish population-health register data; required governed cross-jurisdictional access to sensitive records of older adults.
- **Scientific Reports (2025):** *Growth and sleep outcomes after adenotonsillectomy in pediatric mild sleep-disordered breathing* — used data from the Pediatric Adenotonsillectomy Trial for Snoring (PATS); required consent-governed access to records of minors under IRB protocol.

The architecture is designed to be **institution-agnostic**: teams at different hospitals, research universities, or collaborative registries can evaluate and adapt it without adopting a specific vendor stack or having access to the original protected datasets.

---

## 2. The Governing Problem

Both studies above faced the same four-part constraint that this architecture addresses:

| Constraint | Nature Aging context | Scientific Reports context |
|---|---|---|
| **Raw-data restriction** | UK Biobank and Swedish register data cannot leave their respective controlled-access environments in raw form | PATS trial data is consent-governed; access requires IRB approval and data-use agreement |
| **Cross-jurisdictional rules** | UK data (UK GDPR / Data Protection Act 2018) + Swedish data (Patientdatalag 2008:355) = two different legal regimes for the same analysis | US pediatric clinical data (HIPAA + IRB) must remain within approved access scope; export outside the protocol is not permitted |
| **Sensitive-subject category** | Older-adult population health, including neurological outcomes | Pediatric records (records of minors require heightened protection) |
| **Analytical value vs. exposure tradeoff** | The scientific question (infection–epilepsy association) requires individual-level linkage, but the output (risk estimate) must not expose raw records | Statistical analysis of growth and sleep outcomes requires access to full longitudinal records, but only aggregate or de-identified outputs may be reported |

The architecture below provides a layered response to all four constraints.

---

## 3. Four-Layer Architecture

```
┌───────────────────────────────────────────────────────────────┐
│  LAYER 4: Output Review and Compliance Documentation          │
│  Aggregate outputs · audit sign-off · publication checklist   │
├───────────────────────────────────────────────────────────────┤
│  LAYER 3: Privacy-Preserving Transformation                   │
│  FHE-encrypted computation · DP-bounded aggregation ·         │
│  LLM leakage controls (if AI tooling is used)                 │
├───────────────────────────────────────────────────────────────┤
│  LAYER 2: Access Control and Governance                        │
│  Role matrix · DUA/IRB scope enforcement · audit log ·        │
│  data minimization checkpoint                                 │
├───────────────────────────────────────────────────────────────┤
│  LAYER 1: Data Intake and Classification                       │
│  Source identification · sensitivity classification ·          │
│  legal basis mapping · intake checklist                       │
└───────────────────────────────────────────────────────────────┘
                      ↑ Protected source data
                 (never leaves controlled environment
                  in raw form beyond approved access scope)
```

---

### Layer 1 — Data Intake and Classification

**What this layer does:** Before any data enters the analysis workflow, it is formally classified by sensitivity category, legal basis, jurisdiction, and permitted use scope. This layer produces a written intake record that persists through the workflow.

**Checklist items:**

- [ ] Identify all data sources and the institution or registry that controls each.
- [ ] Classify each source by sensitivity category:
  - Health/medical (HIPAA PHI · GDPR Art. 9 · Patientdatalag)
  - Pediatric (HIPAA + heightened consent requirements)
  - Population registry (country-specific access laws)
  - Genomic / biobank (institutional access committee approval required)
- [ ] Document the legal basis for access (consent, legitimate interest, statutory research exception, DUA, IRB protocol number).
- [ ] Record the permitted use scope: which research questions, which analysis steps, which output types are within scope.
- [ ] Record the data retention and deletion schedule.
- [ ] Identify any cross-border transfer that would occur and confirm the lawful transfer mechanism.

**Nature Aging application:**  
Two intake records required: one for UK Biobank data (legal basis: UK Biobank access application; transfer mechanism: data accessed within UK Biobank environment, derived statistics extracted); one for Swedish register data (legal basis: Swedish ethical review approval + Patientdatalag research exception; transfer mechanism: Statistics Sweden extract under formal application). Cross-border analysis outputs only — raw records do not transfer between jurisdictions.

**Scientific Reports application:**  
One intake record: PATS trial data (legal basis: IRB protocol for secondary analysis; access scope: growth and sleep outcomes variables for the pediatric snoring cohort; retention: per protocol; no cross-border transfer — data remains within the consented US research scope).

---

### Layer 2 — Access Control and Governance

**What this layer does:** Defines who may access what data, in what form, for what purpose, and produces an audit log of every access event.

**Role matrix (template — adapt to specific study):**

| Role | Data accessible | Permitted operations | Access method | Audit requirement |
|---|---|---|---|---|
| Principal investigator | Analysis-ready derived dataset (not raw records) | Statistical query, model training on derived features | Secure compute environment only | Log all queries |
| Data analyst / statistician | Derived features, aggregate outputs | Statistical analysis, quality checks | Secure compute environment only | Log all queries |
| Compliance / IRB reviewer | Access log, output review materials | Audit, approval/rejection of outputs | Read-only audit interface | Log all access |
| External collaborator | Aggregate outputs only (post-review) | Read, cite | Shared output repository (no raw access) | Log all downloads |
| AI / LLM tool | No direct access to identifiable records | Operates only on derived, non-identifying features | Restricted API scope; see Layer 3 LLM controls | Full prompt and response log |

**Data minimization checkpoint:**  
Before data moves into any computation step, verify:
- [ ] Only the variables required for the specific analysis step are in scope (variable minimization).
- [ ] Only the records required for the specific analysis step are in scope (record minimization).
- [ ] All direct identifiers (name, address, date of birth, patient ID) are suppressed or pseudonymized before computation if not analytically necessary.

**Audit log schema:**

```json
{
  "event_id": "<uuid>",
  "timestamp": "<ISO-8601>",
  "actor_role": "<role from matrix above>",
  "action": "<QUERY | ACCESS | EXPORT | REVIEW | AI_CALL>",
  "data_scope": "<dataset or variable list accessed>",
  "legal_basis_reference": "<IRB protocol / DUA number>",
  "output_produced": "<description or null>",
  "review_status": "<PENDING | APPROVED | REJECTED>"
}
```

See `governance-templates/audit-log-template.md` for the full schema.

---

### Layer 3 — Privacy-Preserving Transformation

**What this layer does:** Applies cryptographic or statistical privacy mechanisms to the computation step so that analytical value is extracted while raw-record exposure is limited or eliminated.

Three mechanisms are available depending on the computation type:

#### 3A. FHE-Encrypted Computation (for feature extraction on medical signals or images)

Use when: the analysis requires computing features from raw records (e.g., image patches, signal segments) but the raw records cannot leave their protected environment.

**How it works:** The source record is encrypted using the CKKS homomorphic encryption scheme. Feature extraction computations run on the ciphertext — the record is never decrypted in the analyst's environment. Only the resulting encrypted feature vector is returned; the analyst decrypts only the features, not the source record.

**Module:** `fhe-feature-extraction/fhe_pipeline.py`

```python
from fhe_pipeline import FHEFeaturePipeline

pipeline = FHEFeaturePipeline(poly_modulus_degree=8192)
encrypted_input = pipeline.encrypt(raw_signal)          # raw signal encrypted at source
features = pipeline.extract_features(encrypted_input)   # extraction runs on ciphertext
result = pipeline.decrypt_features(features)            # only features returned
# raw_signal never appears in analyst environment after encryption step
```

**What the audit log records:** input hash (not input value), encryption scheme parameters, feature extraction function name, output dimensionality.

**Nature Aging relevance:** Population-health records from UK Biobank and Swedish registries include signal-level variables (diagnosis codes, lab values, temporal event sequences). FHE-based feature extraction allows association analysis on derived features without copying raw clinical sequences outside the controlled-access environment.

#### 3B. Differential Privacy — Bounded Aggregation (for statistics and model training)

Use when: the analysis produces aggregate statistics or trains a model on sensitive records, and the output must not allow reconstruction of individual records.

**How it works:** The DP wrapper adds calibrated noise to each gradient step during model training (or to each query result for statistical analysis), guaranteeing a formal (ε, δ)-privacy bound. The epsilon budget tracks cumulative information leakage; training stops when the budget is exhausted.

**Module:** `dp-llm-training/dp_trainer.py`

```python
from dp_trainer import DPTrainer

trainer = DPTrainer(
    model=model,
    optimizer=optimizer,
    data_loader=data_loader,
    target_epsilon=3.0,   # privacy budget (lower = more private)
    target_delta=1e-5,
    max_grad_norm=1.0,
)
trainer.train(epochs=10)  # stops when epsilon budget is exhausted
print(f"Final epsilon: {trainer.current_epsilon:.4f}")
```

**What the audit log records:** target epsilon, target delta, noise multiplier used, steps run, final epsilon consumed, whether budget was exhausted before epoch completion.

**Scientific Reports relevance:** Statistical analysis of PATS pediatric data (growth and sleep outcomes) produces aggregate results (effect estimates, confidence intervals, p-values). DP-bounded aggregation ensures that the published statistics do not allow reconstruction of individual children's records, a heightened requirement given the pediatric sensitivity category.

#### 3C. LLM Leakage Controls (for AI-assisted analysis steps)

Use when: any AI or LLM tool is used within the governed-data workflow — for example, to assist with statistical code review, literature search, documentation drafting, or model interpretation.

**Risk:** LLM tools can exfiltrate sensitive data through prompt contents, retrieval pipelines, log capture, and context carryover between sessions. In a governed research environment, using an external LLM on in-scope data without explicit controls constitutes a potential data-security incident.

**Required controls before introducing any LLM tool:**

- [ ] Run the `llm-leakage-assessment/ASSESSMENT-CHECKLIST.md` for the specific tool and workflow.
- [ ] Confirm the tool operates only on derived, non-identifying features (not on raw records or variables that alone could identify individuals).
- [ ] Verify prompt and response logging is captured in the workflow audit log.
- [ ] Confirm no session-to-session context carryover that could transfer in-scope data outside the approved access scope.
- [ ] Obtain compliance / IRB reviewer sign-off before introducing any LLM tool into the governed workflow.

**Module:** `llm-leakage-assessment/ASSESSMENT-CHECKLIST.md`

---

### Layer 4 — Output Review and Compliance Documentation

**What this layer does:** Before any output leaves the governed environment, it is reviewed against the permitted use scope defined in Layer 1 and approved by the compliance/IRB reviewer role defined in Layer 2.

**Pre-release output review checklist:**

- [ ] Confirm output type is within the permitted scope documented in the Layer 1 intake record.
- [ ] Confirm output does not contain direct identifiers.
- [ ] If output is an aggregate statistic: verify cell sizes are above the minimum threshold required by the governing IRB/DUA (typically n ≥ 5 for US research; ≥ 10 for some European registries).
- [ ] If output is a trained model: verify the DP privacy budget was not exceeded and confirm epsilon/delta parameters meet the IRB-approved privacy guarantee.
- [ ] If output is a feature vector: verify the source record has not been reconstructed and the feature dimensionality does not uniquely identify individuals.
- [ ] Capture reviewer sign-off in the audit log.

**Publication and dissemination checklist:**

- [ ] Confirm the publication does not include individual-level data beyond what is approved.
- [ ] Verify all data-use agreements require acknowledgment/citation of the data source.
- [ ] Confirm all authors have reviewed and approved the data-representation in the manuscript.
- [ ] Archive the Layer 1 intake record, Layer 2 audit log, and Layer 4 review sign-off for the retention period required by the governing IRB/DUA.

---

## 4. Cross-Jurisdiction Compliance Mapping

| Control | HIPAA Security Rule | EU GDPR Art. 9 | Swedish Patientdatalag | NIST Privacy Framework |
|---|---|---|---|---|
| Layer 1 intake and classification | §164.312(a)(1) Access control | Art. 9(2)(j) research exception + DPIA | Ch. 3 — purpose limitation and legal basis | Identify-P: Data Processing Ecosystem |
| Layer 2 role matrix | §164.312(a)(2)(i) Unique user ID | Art. 5(1)(f) integrity and confidentiality | Ch. 5 — access control | Govern-P: Policies and procedures |
| Layer 2 data minimization | §164.312(e)(2)(ii) Encryption (in transit) | Art. 5(1)(c) data minimisation | Ch. 4 — minimum necessary | Control-P: Data Processing |
| Layer 2 audit log | §164.312(b) Audit controls | Art. 30 Records of processing | Ch. 8 — documentation | Protect-P: Data Processing |
| Layer 3A FHE computation | §164.312(a)(2)(iv) Encryption (at rest) | Art. 32 encryption + pseudonymisation | Ch. 5 — technical safeguards | Protect-P: Technical safeguards |
| Layer 3B DP aggregation | §164.512(i) research use + de-identification | Art. 89(1) research with appropriate safeguards | Ch. 3 — statistical output rules | Control-P: Disassociated processing |
| Layer 3C LLM controls | §164.308(a)(5) security awareness | Art. 32 — risk-appropriate technical measures | Ch. 5 — technical safeguards | Protect-P: Cybersecurity safeguards |
| Layer 4 output review | §164.514 de-identification standard | Art. 5(1)(b) purpose limitation | Ch. 6 — disclosure rules | Govern-P: Risk management |

Full NIST control mapping in `docs/compliance/nist-control-mapping.md`.  
HIPAA-specific control mapping in `docs/compliance/hipaa-control-mapping.md` (Day 6 milestone).

---

## 5. Worked Example — Population-Health Registry Study (Nature Aging Pattern)

**Research question:** Does hospital-treated infection in older adults predict elevated epilepsy risk in the subsequent years?

**Data sources:** UK Biobank (UK controlled-access environment) + Swedish population registers (Statistics Sweden extract).

**Architecture walkthrough:**

| Layer | What happens |
|---|---|
| **Layer 1 intake** | Two intake records created: UK Biobank application reference + Swedish ethical review approval number. Permitted scope: ICD diagnosis codes, hospital contact dates, age, sex. No direct identifiers in scope. Cross-border: derived statistics only. |
| **Layer 2 access control** | PI and statistician access derived variables only (ICD codes + event dates, pseudonymized). External collaborators see only regression outputs. Audit log records each query. |
| **Layer 3B DP aggregation** | Logistic regression and Cox proportional hazards models fitted under DP guarantees. Published hazard ratios and confidence intervals represent DP-noisy outputs; individual records not reconstructable from published results. |
| **Layer 4 output review** | Compliance reviewer confirms: no cell below reporting threshold, no individual-level data in manuscript, both data controllers notified of publication. Audit log archived per UK Biobank and Statistics Sweden agreements. |

---

## 6. Worked Example — Pediatric Clinical Trial Secondary Analysis (Scientific Reports Pattern)

**Research question:** Does adenotonsillectomy improve growth and sleep outcomes in children with mild sleep-disordered breathing?

**Data source:** PATS trial data (US — pediatric clinical research, IRB-governed, consent-based).

**Architecture walkthrough:**

| Layer | What happens |
|---|---|
| **Layer 1 intake** | One intake record: IRB protocol number for secondary analysis; permitted scope: growth variables (height, weight, BMI), sleep-study outcomes (AHI, ODI), and treatment assignment. Pediatric sensitivity category flagged. No cross-border transfer. |
| **Layer 2 access control** | Full data accessible only to PI and statistician within IRB-approved secure compute environment. Variable minimization applied: only height, weight, AHI, ODI, treatment arm — no other PHI in scope for this analysis step. Audit log records every access. |
| **Layer 3B DP aggregation** | Mixed-effects regression models for longitudinal growth outcomes fitted under DP; published treatment-effect estimates are DP-bounded. Pediatric sensitivity requires tighter epsilon target (ε ≤ 2.0 recommended given subject age). |
| **Layer 4 output review** | Compliance reviewer confirms: no cell below n=5, no child identifiable from outputs, PATS data-use agreement terms satisfied. Author-contribution statement prepared: data access and statistical analysis roles documented. Audit log archived per PATS DUA. |

---

## 7. Limitations and Scope

- This document is a reference architecture, not a certification or guarantee of compliance. Institutional compliance, legal counsel, and IRB review are required before applying these patterns to real protected data.
- FHE performance on large medical imaging datasets requires validation at scale; the current `fhe_pipeline.py` prototype uses CKKS with synthetic signals and includes a mock-fallback mode when TenSEAL is not installed.
- DP epsilon values must be selected by a qualified privacy engineer in consultation with IRB and legal counsel; the values shown above are illustrative only.
- Future use of real protected clinical or registry data requires separate written authorizations, data-use agreements, and IRB or ethics review where applicable.
- All current prototype module examples use synthetic, public, or no data.

---

## 8. Related Resources in This Repository

| Resource | Path | What it adds |
|---|---|---|
| FHE pipeline (Layer 3A) | `fhe-feature-extraction/fhe_pipeline.py` | Working CKKS implementation for encrypted feature extraction |
| FHE quick-start | `fhe-feature-extraction/examples/basic_usage.py` | Runnable demo on synthetic medical signal |
| DP trainer (Layer 3B) | `dp-llm-training/dp_trainer.py` | DP training wrapper with RDP privacy accounting |
| DP demo | `dp-llm-training/examples/demo_training.py` | Training loop with per-step epsilon reporting |
| LLM checklist (Layer 3C) | `llm-leakage-assessment/ASSESSMENT-CHECKLIST.md` | 35-item structured assessment for LLM tools on regulated data |
| Data minimization template (Layer 2) | `governance-templates/data-minimization-checklist.md` | HIPAA/GDPR-aligned data minimization workflow |
| NIST control mapping (Layer 4) | `docs/compliance/nist-control-mapping.md` | Control-by-control NIST mapping |

---

## 9. Citation

If you use this architecture in your research or institutional implementation, please cite the foundational papers that grounded its design:

```bibtex
@article{nature_aging_epilepsy_2025,
  title   = {Hospital-treated infectious diseases and the risk of epilepsy in older age},
  journal = {Nature Aging},
  year    = {2025},
  doi     = {10.1038/s43587-024-00783-8}
}

@article{scientific_reports_pediatric_sleep_2025,
  title   = {Growth and sleep outcomes after adenotonsillectomy in pediatric mild sleep-disordered breathing},
  journal = {Scientific Reports},
  year    = {2025}
}
```

Full BibTeX for all foundation papers in [`CITATION.md`](../CITATION.md).
