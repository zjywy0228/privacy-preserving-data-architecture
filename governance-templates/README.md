# Governance Templates

Reusable governance artifacts for institutions adopting privacy-preserving
computation methods under biomedical research oversight and regulatory compliance.

All templates are illustrative starting points. Adapt them to your institution's
specific IRB format, data-use agreement requirements, and applicable regulations
before submission or deployment.

## Contents

| Template | Purpose | Applicable controls |
|---|---|---|
| [`irb-amendment-template.md`](irb-amendment-template.md) | Amend an existing IRB protocol to add FHE / DP / federated learning | 45 CFR 46, HIPAA §164.308(a)(1) |
| [`derived-variable-lineage-template.md`](derived-variable-lineage-template.md) | Document data-lineage for derived variables exported from a controlled-access environment | NIST Privacy Framework CT.DM-P4 |
| [`pre-export-output-review-checklist.md`](pre-export-output-review-checklist.md) | Pre-export review checklist for analytical outputs leaving a secure enclave | NIST CSF PR.DS-5, HIPAA §164.312(b) |
| [`data-minimization-checklist.md`](data-minimization-checklist.md) | Data-minimization assessment before a new analysis pipeline is approved | NIST Privacy Framework CT.PO-P1, GDPR Art. 5(1)(c) |
| [`synthetic-data/`](synthetic-data/) | Reproducible synthetic clinical dataset generator for testing — no PHI | HIPAA §164.308(a)(1), NIST AI RMF MAP 2.1 |

## How to use

1. **IRB amendment:** Copy `irb-amendment-template.md`, fill all `[BRACKETED]`
   fields, remove inapplicable sections, and submit via your institution's IRB
   submission portal. Reference `docs/compliance/nist-control-mapping.csv` for
   the relevant NIST control IDs to include in the software-inventory section.

2. **Synthetic data for testing:** Use `synthetic-data/generate_synthetic_clinical.py`
   to generate reproducible test datasets that match the distributional shape of
   your target population without using real records. See
   [`synthetic-data/README.md`](synthetic-data/README.md) for full options.

3. **Pre-export review:** Run through `pre-export-output-review-checklist.md`
   before releasing any aggregate statistics, model outputs, or derived variables
   from a controlled-access environment.

## Federal alignment

| Framework | Key articles/controls | Templates |
|---|---|---|
| HIPAA Security Rule | §164.308(a)(1) Administrative Safeguards | IRB amendment, synthetic data |
| NIST Privacy Framework v1.0 | CT.PO-P1, CT.PO-P3, CT.DM-P4, CT.DM-P8 | All templates |
| NIST CSF 2.0 | GV.PO-01, PR.DS-5 | Pre-export checklist, data minimization |
| 45 CFR 46 (Common Rule) | §46.110 Expedited review | IRB amendment |
| GDPR | Art. 5(1)(c), Art. 25, Art. 89 | Data minimization, lineage |
