# IRB Amendment Template: Adding Privacy-Preserving Analytics to an Approved Protocol

Use this template when amending an existing Institutional Review Board (IRB) protocol to incorporate homomorphic-encryption (HE), differential privacy (DP), or controlled-access architectural controls into a research data-analysis pipeline. Fill in all `[BRACKETED]` fields; delete sections that do not apply.

---

## Section 1 — Protocol Identification

| Field | Value |
|---|---|
| IRB Protocol Number | [e.g., IRB-2024-00123] |
| Protocol Title | [Full title as approved] |
| Principal Investigator | [Name, Title, Department, Institution] |
| Amendment Number | [e.g., Amendment 3] |
| Submission Date | [YYYY-MM-DD] |
| Anticipated Implementation Date | [YYYY-MM-DD] |

---

## Section 2 — Nature of the Amendment

> Summarise the change in one or two sentences. Be specific about the technical mechanism being added.

**Summary:** This amendment adds [FHE feature extraction / DP noise injection / controlled-access query layer] to the data-processing pipeline described in Section [N] of the approved protocol. No changes are made to study objectives, participant recruitment, consent procedures, or data-collection instruments.

**Reason for amendment:** [e.g., The original protocol transmitted de-identified image features to a shared analysis server. The amendment replaces cleartext feature vectors with fully homomorphic encrypted (FHE) feature representations, eliminating the need to expose raw derived features outside the data-owner environment.]

---

## Section 3 — Description of Technical Changes

### 3.1 Prior Data-Flow (Approved Protocol)

Describe the original pipeline at a level the IRB can evaluate:

1. [Step 1, e.g., Raw electronic health records extracted to secure analysis workstation under data-use agreement]
2. [Step 2, e.g., De-identified records transferred to shared analytics environment via encrypted channel]
3. [Step 3, e.g., Feature vectors stored in plaintext for model training]

### 3.2 Amended Data-Flow

Describe what changes and what stays the same:

1. [Step 1 — unchanged, e.g., Raw records extracted to secure workstation — no change]
2. [Step 2 — changed, e.g., De-identified records processed locally; only FHE-encrypted feature vectors leave the workstation. The encryption key never leaves the data-owner environment.]
3. [Step 3 — changed, e.g., DP noise (ε = X, δ = Y) applied at gradient aggregation; encrypted feature vectors used on shared compute without exposing plaintext values.]

### 3.3 Privacy-Preserving Methods Introduced

For each method added, complete the table:

| Method | Implementation | Privacy Parameter | Verification |
|---|---|---|---|
| Fully Homomorphic Encryption (FHE) | [e.g., TenSEAL CKKS scheme, 128-bit security] | N/A — no plaintext crosses boundaries | Decryption key held exclusively by [role/system] |
| Differential Privacy (DP) | [e.g., Opacus Gaussian Mechanism, per-epoch noise] | ε = [X], δ = [Y] | Privacy accountant log attached as Appendix A |
| Controlled-Access Query Layer | [e.g., parameterised SQL with audit log] | Query rate limit: [N]/hour | Audit log retained for [duration] per [policy] |

---

## Section 4 — Impact on Human Subjects Protections

### 4.1 Risk Assessment

| Risk Category | Prior Protocol | Amended Protocol | Change |
|---|---|---|---|
| Re-identification from feature vectors | Low (de-identified features) | Lower (FHE-encrypted features) | Reduced |
| Data breach at analysis server | Possible (plaintext features present) | Lower (only ciphertext at server) | Reduced |
| Model memorisation of training records | Possible | Reduced (DP noise applied) | Reduced |
| Consent scope | [current scope] | Unchanged | None |
| Data-sharing obligations | [current] | Unchanged | None |

**Summary:** The amendment introduces no new risks to participants. The privacy-preserving controls reduce the residual re-identification risk present in the original pipeline. Benefits to participants are unchanged.

### 4.2 Informed-Consent Impact

- [ ] Consent language is unchanged. The amendment is a back-end technical control that does not affect what participants were told about data use.
- [ ] Consent language requires revision. Attach revised consent form as Appendix B and describe changes below.

[If consent revision is required, describe here.]

### 4.3 Vulnerable Populations

Not affected by this amendment. [Or describe any impact if applicable.]

---

## Section 5 — Data Security Section Update

Replace Section [N.N] ("Data Security") of the approved protocol with the following text:

> **Data Security (Amended):** Participant-derived data are processed under a privacy-preserving architecture that applies [FHE / DP / controlled-access controls] as described in Amendment [N]. Raw or de-identified records remain within the data-owner access-controlled environment. Only [encrypted outputs / aggregate statistics with DP noise] cross system boundaries. Access logs are retained for [duration] and reviewed [quarterly / per audit cycle]. Technical controls conform to HIPAA Security Rule 45 CFR Part 164 Subpart C and NIST SP 800-188.

---

## Section 6 — Protocol Sections Affected

List every section of the approved protocol that changes as a result of this amendment:

| Section | Title | Change Description |
|---|---|---|
| [N.N] | Data Security | Replaced with amended text (Section 5 above) |
| [N.N] | Statistical Analysis Plan | Added note that DP-trained model outputs carry a formal (ε, δ) guarantee |
| [N.N] | Data Sharing / Transfer | Updated to reflect that only ciphertext or DP-aggregate statistics are transferred |

Sections not listed above are unchanged.

---

## Section 7 — Supporting Documentation Checklist

Attach the following to this amendment submission:

- [ ] Updated protocol narrative (track-changes version)
- [ ] System architecture diagram showing amended data flow
- [ ] Privacy budget accounting log (if DP is added) — format per `dp-llm-training/` audit-log schema
- [ ] FHE key-management procedure (if HE is added) — one-page description of key generation, storage, and rotation
- [ ] Updated data-use agreement (DUA) or confirmation from data provider that amendment is within DUA scope
- [ ] Revised consent form (if Section 4.2 second box checked)
- [ ] Institution-specific IRB cover sheet

---

## Section 8 — Investigator Certification

By submitting this amendment, the principal investigator certifies that:

1. The described changes are accurately represented.
2. No human-subjects activities under the amended protocol will begin until IRB approval is granted.
3. All team members who will implement the amended pipeline have reviewed the technical procedures.
4. The privacy-preserving controls described have been tested in a non-production environment prior to deployment on participant data.

| Role | Name | Signature | Date |
|---|---|---|---|
| Principal Investigator | | | |
| Co-Investigator (if applicable) | | | |
| Data Security Officer (if required) | | | |

---

## Appendix A — Privacy Budget Accounting Log (DP only)

If differential privacy is introduced, attach the privacy accountant output. Minimum required fields per training epoch:

```json
{
  "epoch": 1,
  "epsilon": 0.42,
  "delta": 1e-5,
  "mechanism": "Gaussian",
  "noise_multiplier": 1.1,
  "max_grad_norm": 1.0,
  "cumulative_epsilon": 0.42,
  "timestamp": "2026-01-15T14:32:00Z"
}
```

The audit-log schema is defined in `dp-llm-training/audit_log_schema.json`.

---

## References

- HIPAA Security Rule, 45 CFR Part 164, Subpart C — Technical Safeguards
- NIST SP 800-188, *De-Identifying Government Datasets* (2nd draft)
- NIST AI RMF 1.0, GOVERN 6.1 — Privacy risk management policies and procedures
- Privacy-Preserving Data Sharing Agreement (PPDSA) Framework, HHS Office of the National Coordinator
- Common Rule, 45 CFR Part 46 — Federal Policy for the Protection of Human Subjects
- See also: `docs/compliance/nist-control-mapping.csv`, `docs/compliance/hipaa-control-mapping.md`
