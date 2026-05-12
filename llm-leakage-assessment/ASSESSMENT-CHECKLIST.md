# LLM Data-Leakage Assessment Checklist

Structured assessment methodology for institutions deploying large language models (LLMs) or AI-assisted workflows on sensitive personal or institutional data.

Based on the threat taxonomy in:
> Zhang et al., "Assessment Methods and Protection Strategies for Data Leakage Risks in Large Language Models," IEEE, 2025.

---

## How to Use This Checklist

Work through each section before deploying an LLM system on sensitive data. For each item:
- **PASS**: control is in place and verified
- **FAIL**: control is absent — note the mitigation action
- **N/A**: item does not apply to this deployment
- **RISK-ACCEPTED**: gap is known, documented, and accepted by the data owner

Repeat assessment when: model version changes, new data categories are added, workflow integrations change, or after any suspected exposure incident.

---

## Section 1: Training Data Assessment

*Applies if you are fine-tuning or training a model on institutional data.*

| # | Check | Status | Notes |
|---|---|---|---|
| 1.1 | Training dataset has been inventoried for sensitive data categories (PII, PHI, financial, proprietary) | | |
| 1.2 | Each sensitive category has a documented legal basis for inclusion in training | | |
| 1.3 | Training data has been de-identified or anonymised where possible before use | | |
| 1.4 | Differential privacy (DP) training has been evaluated; if not applied, documented reason exists | | |
| 1.5 | Target epsilon and delta for DP training have been chosen and documented | | |
| 1.6 | Membership inference attack has been tested on the trained model before deployment | | |
| 1.7 | Training-data extraction attack has been tested (e.g., Carlini et al. method) | | |
| 1.8 | Training data access log exists (who ingested what, when, from which source) | | |

---

## Section 2: Inference / Deployment Assessment

*Applies to any model accepting prompts or queries from users or automated systems.*

| # | Check | Status | Notes |
|---|---|---|---|
| 2.1 | System prompt does not contain sensitive data that should not be revealed to end users | | |
| 2.2 | System prompt injection defences are in place (tested against known prompt-injection patterns) | | |
| 2.3 | Model output is filtered before return to caller (no verbatim sensitive data in outputs) | | |
| 2.4 | Retrieval-Augmented Generation (RAG) document store has access control — model only retrieves documents the querying user is authorized to see | | |
| 2.5 | RAG retrieved chunks are logged; log shows what source material influenced each response | | |
| 2.6 | Output logging is in place; logs do not themselves contain unredacted sensitive data | | |
| 2.7 | Rate limiting and query monitoring are configured to detect bulk extraction attempts | | |
| 2.8 | Model API keys and credentials are rotated on a documented schedule | | |

---

## Section 3: Tool and Agent Pipeline Assessment

*Applies to agentic LLM workflows with access to tools, APIs, or internal systems.*

| # | Check | Status | Notes |
|---|---|---|---|
| 3.1 | Each tool the LLM can invoke has been enumerated with its data-access scope | | |
| 3.2 | Tool access is least-privilege: LLM can only invoke tools needed for its stated purpose | | |
| 3.3 | Tool calls and their parameters are logged with the user/session identity | | |
| 3.4 | Tool outputs returned to the model are assessed for sensitive content before inclusion in context | | |
| 3.5 | Multi-agent pipelines have documented trust boundaries: which agent can pass data to which | | |
| 3.6 | Context window contents are not persisted beyond the session without documented justification | | |
| 3.7 | Long-term memory components (vector stores, databases) have access control and retention limits | | |

---

## Section 4: Model and Weights Access Control

| # | Check | Status | Notes |
|---|---|---|---|
| 4.1 | Model weights are stored in access-controlled storage (not publicly accessible if trained on sensitive data) | | |
| 4.2 | Model serving infrastructure is network-segmented from systems holding raw sensitive data | | |
| 4.3 | Model-card or equivalent documentation states what data the model was trained on | | |
| 4.4 | Model versioning is in place; rollback to a previous version is possible | | |
| 4.5 | A process exists to retrain or patch the model if a data-exposure incident occurs | | |

---

## Section 5: Governance and Documentation

| # | Check | Status | Notes |
|---|---|---|---|
| 5.1 | A data-handling policy for LLM deployments has been approved by the data owner | | |
| 5.2 | Relevant data-use agreements, IRB approvals, or DPIAs have been reviewed for compatibility with LLM use | | |
| 5.3 | An incident-response procedure exists for suspected LLM-related data exposure | | |
| 5.4 | Staff with access to the LLM system have received training on data-leakage risks | | |
| 5.5 | A periodic re-assessment schedule is documented | | |

---

## Assessment Summary Template

```
System Name: ___________________________________________
Assessment Date: ______________________________________
Assessed By: __________________________________________
Model / Version: ______________________________________
Data Categories in Scope: _____________________________

Section 1 (Training): PASS / FAIL / N/A — notes:
Section 2 (Inference): PASS / FAIL / N/A — notes:
Section 3 (Tools / Agents): PASS / FAIL / N/A — notes:
Section 4 (Weights Access): PASS / FAIL / N/A — notes:
Section 5 (Governance): PASS / FAIL / N/A — notes:

Open items requiring remediation:
1.
2.
3.

Next review date: ______________________________________
Approved by (data owner): _____________________________
```
