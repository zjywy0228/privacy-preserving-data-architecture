# NIST Control Mapping for Privacy-Preserving AI Analytics

Maps the architecture patterns in this repository to NIST framework controls relevant to sensitive-data AI deployments.

---

## NIST Privacy Framework (PF) Mapping

| Architecture Pattern | PF Function | PF Category | Control Description |
|---|---|---|---|
| FHE feature extraction | PROTECT (PR) | Data Processing Policies (PR.PO) | Process data using privacy-by-design approaches that limit raw-data exposure |
| FHE feature extraction | PROTECT (PR) | Disassociated Processing (PR.DS) | Use techniques (tokenisation, encryption, anonymisation) to disassociate data from individuals during processing |
| DP training wrapper | PROTECT (PR) | Data Processing Policies (PR.PO) | Apply differential privacy to bound individual-level information in model outputs |
| LLM leakage assessment | IDENTIFY (ID) | Data Processing Ecosystem Risk Management (ID.DE) | Identify, assess, and manage privacy risks in AI/data processing pipelines |
| Data minimization checklist | PROTECT (PR) | Data Processing Policies (PR.PO) | Limit data collection and processing to what is necessary for the stated purpose |
| Audit log template | GOVERN (GV) | Policies, Processes, and Procedures (GV.PO) | Maintain policies for data processing activities and accountability |

---

## NIST AI Risk Management Framework (AI RMF) Mapping

| Architecture Pattern | AI RMF Function | Category | Subcategory |
|---|---|---|---|
| LLM leakage assessment | MAP | AI Risk Identification | Map.1.1 — Context is established for the AI risk assessment |
| LLM threat taxonomy | MAP | AI Risk Identification | Map.2.2 — Scientific findings related to AI are identified and communicated |
| DP training wrapper | MEASURE | AI Risk Analysis | Measure.2.5 — Privacy risks are evaluated and documented |
| FHE feature extraction | MANAGE | AI Risk Treatment | Manage.2.2 — Mechanisms to sustain the value of deployed AI systems are evaluated |
| Assessment checklist | GOVERN | AI Risk Culture | Govern.1.4 — Organizational teams are committed to the AI risk management process |

---

## NIST Adversarial ML Report (2025) Mapping

| Architecture Pattern | Attack Class Addressed | NIST AML Reference |
|---|---|---|
| DP training wrapper | Training-data extraction, membership inference | Section 2.5 — Extraction attacks |
| LLM leakage assessment | Prompt injection, context leakage | Section 3.2 — Inference-time attacks |
| LLM threat taxonomy | Model inversion, membership inference | Section 2.3 — Inversion attacks |
| FHE feature extraction | Raw-data exposure during computation | Section 4.1 — Data-poisoning and exposure |

---

## NIST Cybersecurity Framework 2.0 (CSF 2.0) Mapping

| Architecture Pattern | CSF Function | Category |
|---|---|---|
| Audit log template | IDENTIFY | ID.AM — Asset Management |
| Data minimization checklist | PROTECT | PR.DS — Data Security |
| DP training wrapper | PROTECT | PR.DS — Data Security |
| LLM leakage assessment | IDENTIFY | ID.RA — Risk Assessment |
| Assessment checklist | RESPOND | RS.AN — Incident Analysis |
