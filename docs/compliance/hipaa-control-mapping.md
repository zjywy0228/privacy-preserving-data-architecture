# HIPAA Security Rule — Architecture Control Mapping

**Version:** 1.0  
**Last updated:** 2026-05-17  
**Frameworks:** 45 CFR Part 164 (HIPAA Security Rule)  
**Modules covered:** `fhe-feature-extraction`, `dp-llm-training`, `llm-leakage-assessment`, `governance-templates`, `architectures`

---

## Purpose

This document maps the technical and administrative controls in this repository to the
relevant safeguard standards and implementation specifications of the HIPAA Security Rule
(45 CFR Part 164, Subpart C).

Each row identifies a specific architecture pattern or module capability and the
corresponding HIPAA requirement. The *R/A* column marks whether the specification is
**Required (R)** or **Addressable (A)**.

> **Scope note:** This mapping reflects the *design intent* of the architecture
> patterns, not a formal compliance certification. Organizations deploying these
> patterns in workflows that handle Protected Health Information (PHI) must conduct
> their own risk analysis and engage qualified compliance reviewers.

---

## 1. Technical Safeguards — §164.312

### §164.312(a)(1) — Access Control Standard

Implement technical policies to allow access to ePHI only to authorized persons or
software programs.

| R/A | Implementation Spec | Architecture Pattern / Module | Notes |
|---|---|---|---|
| R | Unique user identification | `governance-templates/` — access-control role matrix | Role-based access matrix template assigns unique roles; each data-access decision is logged with user identity |
| A | Automatic logoff | FHE session design in `fhe_pipeline.py` | CKKS context and key material are scoped to the computation session; no persistent plaintext state after session close |
| A | Encryption and decryption | `fhe-feature-extraction/fhe_pipeline.py` | Raw biomedical input encrypted at source with TenSEAL CKKS; decryption occurs only for the derived feature vector, never for raw input |
| R | Emergency access procedure | `governance-templates/` — incident-response pattern | Governance template includes a break-glass access procedure with mandatory audit-log entry |

### §164.312(b) — Audit Controls Standard

Hardware, software, and/or procedural mechanisms that record and examine activity in
information systems that contain or use ePHI.

| R/A | Implementation Spec | Architecture Pattern / Module | Notes |
|---|---|---|---|
| R | Audit controls | `fhe_pipeline.py` — `DataMinimizationPipeline.get_audit_log()` | Per-request provenance log records: input shape, encrypted fields, computation type, output shape, timestamp |
| R | Audit controls | `dp-llm-training/budget_accountant.py` — `BudgetAccountant.save_log()` | JSON audit log records: epoch, epsilon, delta, loss, budget fraction, timestamp |
| R | Audit controls | `governance-templates/` — audit-log template | Structured schema for data-access records; includes stated purpose, retention period, disposal policy |
| R | Audit controls | `llm-leakage-assessment/assessment_runner.py` | Assessment runs produce PASS/FAIL/PARTIAL result records per test case; reproducible via MockModel in CI |

### §164.312(c)(1) — Integrity Standard

Protect ePHI from improper alteration or destruction.

| R/A | Implementation Spec | Architecture Pattern / Module | Notes |
|---|---|---|---|
| A | Mechanism to authenticate ePHI | FHE ciphertext integrity | TenSEAL CKKS ciphertexts detect tampering; any bit corruption produces decryption errors rather than silent wrong output |
| A | Mechanism to authenticate ePHI | DP training output integrity | Training results are paired with epsilon/delta accounting log; output without corresponding audit log should be treated as unverified |

### §164.312(d) — Person or Entity Authentication Standard

Implement procedures to verify that a person or entity seeking access to ePHI is the
one claimed.

| R/A | Implementation Spec | Architecture Pattern / Module | Notes |
|---|---|---|---|
| R | Person or entity authentication | `governance-templates/` — access-control role matrix | Template requires authenticated identity before granting any data-access role; authentication mechanism is deployment-specific |
| R | Person or entity authentication | Biomedical reference architecture — Layer 2 | Access-control layer in the four-layer architecture includes DUA/IRB scope enforcement and identity verification checkpoint |

### §164.312(e)(1) — Transmission Security Standard

Guard against unauthorized access to ePHI transmitted over an electronic communications
network.

| R/A | Implementation Spec | Architecture Pattern / Module | Notes |
|---|---|---|---|
| A | Integrity controls | FHE transmission model | Ciphertext transmitted between compute nodes; raw input never traverses the network in plaintext |
| A | Encryption | `fhe-feature-extraction/fhe_pipeline.py` — ciphertext computation | All computation on biomedical features occurs over ciphertext; §164.312(e)(2)(ii) addressable spec satisfied by design |

---

## 2. Administrative Safeguards — §164.308 (Selected)

The architecture patterns support (but do not replace) the following administrative
safeguard requirements:

| Safeguard | §164.308 Ref | Architecture Support |
|---|---|---|
| Risk analysis | §164.308(a)(1)(ii)(A) | `llm-leakage-assessment/` — systematic threat taxonomy + assessment runner; `nist-control-mapping.csv` — risk-pattern inventory |
| Risk management | §164.308(a)(1)(ii)(B) | DP training budget enforcement halts training when target epsilon is reached, bounding re-identification risk |
| Audit log review | §164.308(a)(1)(ii)(D) | `BudgetAccountant.save_log()` and `DataMinimizationPipeline.get_audit_log()` produce machine-readable logs suitable for periodic review |
| Access management | §164.308(a)(4) | `governance-templates/` — access-control role matrix; biomedical reference architecture Layer 2 |
| Security incident response | §164.308(a)(6) | Governance templates include LLM data-exposure incident response playbook |
| Contingency plan | §164.308(a)(7) | Audit log retention template includes documented retention and disposal schedule |

---

## 3. Privacy Rule Alignment — §164.514 De-identification

Two safe-harbor methods exist under §164.514(b): expert determination and the
18-identifier removal standard. This repository supports de-identification workflows as
follows:

| De-identification Layer | Architecture Support |
|---|---|
| FHE output minimization | Only derived feature vector is decrypted; 18 PHI identifiers in the raw input are never exposed in output |
| DP noise injection | Differential privacy noise bounds the re-identification probability of any released statistical output |
| Data minimization checklist | `governance-templates/data-minimization-checklist.md` — purpose-limitation and proportionality checkpoint before each data-access step |
| Pre-export output review | Governance checklist requires review of aggregate outputs before they leave the privacy-preserving computation environment |

---

## 4. Research Exception — §164.512(i)

Studies using datasets such as UK Biobank, Swedish population registries, and pediatric
clinical trial data (see biomedical reference architecture) typically rely on the
§164.512(i) research exception or an equivalent IRB approval and data-use agreement.

The architecture supports research workflows by:

- Maintaining a per-study intake record documenting the legal basis for access (Layer 1 of the biomedical reference architecture).
- Enforcing the approved use scope through the role matrix and output-review gate.
- Generating an audit log that can be produced for IRB review or HIPAA compliance verification.

---

## 5. Limitations

- This document covers the HIPAA **Security Rule** (45 CFR Part 164 Subpart C). HIPAA Privacy Rule obligations (Subpart E) are not mapped here.
- The FHE and DP modules are prototype implementations. A production deployment must undergo a formal security assessment before handling real PHI.
- The HIPAA Security Rule applies only when an organization qualifies as a Covered Entity or Business Associate under 45 CFR Part 160. Confirm applicability before relying on this mapping.

---

## References

- 45 CFR Part 164 — HIPAA Security and Privacy Rules: <https://www.hhs.gov/hipaa/for-professionals/security/index.html>
- HHS HIPAA Security Rule Summary: <https://www.hhs.gov/sites/default/files/ocr/privacy/hipaa/administrative/securityrule/securityruleguidance.pdf>
- NIST SP 800-66r2 — Implementing the HIPAA Security Rule (2023): <https://doi.org/10.6028/NIST.SP.800-66r2>
- `docs/compliance/nist-control-mapping.csv` — companion NIST AI RMF / Privacy Framework / CSF 2.0 mapping
