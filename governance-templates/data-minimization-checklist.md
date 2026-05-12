# Data Minimization Checklist for Biomedical and Regulated-Data Analytics

Workflow checklist for research teams and data engineers setting up analytics pipelines on sensitive health or scientific data. Implements the minimum-necessary principle required by HIPAA, GDPR Article 5(1)(c), and equivalent frameworks.

---

## Pre-Analysis Phase

- [ ] **Define the research question precisely.** Write a one-sentence statement of what the analysis must answer.
- [ ] **List the data elements required.** For each variable in the analysis, document why it is necessary for the stated question.
- [ ] **Identify what is NOT required.** Explicitly exclude identifiers (name, address, date of birth, medical record number) unless the question requires them.
- [ ] **Obtain a data-use agreement or IRB approval** covering the specific dataset, analysis purpose, and output types.
- [ ] **Review data-access controls.** Confirm that only the analysis team members who need access have it, and that access is revokable.

---

## Data Ingestion Phase

- [ ] **Receive data in a dedicated, access-controlled environment.** Raw sensitive data should not land in shared storage or a general-purpose file system.
- [ ] **Verify data provenance.** Confirm the dataset received matches the approved DUA/IRB scope (source, date, cohort).
- [ ] **Apply de-identification or pseudonymisation** before broad-scope analysis. Direct identifiers should be removed or replaced at ingestion unless the specific analytical step requires them.
- [ ] **Log ingestion event.** Record: who ingested, from which source, when, and the record count.
- [ ] **Do not copy or duplicate raw sensitive data** beyond the minimum needed for the analysis.

---

## Analysis Phase

- [ ] **Operate on derived variables, not raw records, where possible.** If the question requires age, use age; do not carry date of birth through the entire pipeline.
- [ ] **Apply transformation logging.** Each pipeline step that transforms the data should be documented with: input format, transformation applied, output format.
- [ ] **Intermediate outputs should not contain raw identifiers** unless required for the next step.
- [ ] **Statistical outputs with small cell sizes should be suppressed** or noise-added before release (k-anonymity / cell suppression rules per data-use agreement).
- [ ] **Audit access during analysis.** Who queried which table or file, and when.

---

## Output Phase

- [ ] **Review outputs before release** for residual direct or indirect identifiers.
- [ ] **Apply output-review checklist** (see below) before sharing results with collaborators outside the controlled environment.
- [ ] **Do not include raw data in publications or reports.** Only aggregate statistics, model parameters, or explicitly de-identified summaries.
- [ ] **Log output release event.** Record: what was released, to whom, when, and the authorising data-owner approval.

---

## Output Review Checklist

Before sharing any result derived from sensitive data:

| Check | Pass? |
|---|---|
| Output contains no direct identifiers (name, ID, address, DOB) | |
| Output contains no small-cell counts below the agreed suppression threshold | |
| Output does not include raw data rows (only aggregates or model outputs) | |
| Output release is covered by the existing DUA / IRB approval scope | |
| Data owner has approved this output for release | |

---

## Retention and Deletion

- [ ] Define the retention period for raw data at the start of the project.
- [ ] After analysis is complete, delete raw data from the analysis environment according to the agreed retention schedule.
- [ ] Log deletion event: what was deleted, when, and by whom.
- [ ] Confirm that backups, caches, and intermediate files have also been purged.

---

## References

- HIPAA Minimum Necessary Standard (45 CFR § 164.502(b))
- GDPR Article 5(1)(c) — Data Minimisation
- NIST Privacy Framework Core — CT.DM (Data Management)
- HHS Office for Civil Rights — Guidance on Minimum Necessary Standard
