# Pre-Export Output Review Checklist

A structured checklist for researchers and data engineers to complete before any
result, model output, summary table, figure, or derived dataset leaves a
controlled-access analysis environment.

Designed for controlled-access biomedical and scientific data environments where:
- Source data is held in a nationally administered secure enclave (e.g., national
  patient registry, biobank, scientific infrastructure facility).
- Results must pass a governance review before being transmitted to collaborators,
  submitted to journals, or included in public repositories.
- Multiple reviewers (analyst, data custodian, IRB/ethics point of contact) may
  share sign-off responsibility.

Modeled on output-review practice in population-registry studies (e.g., studies
using Swedish national registers or UK Biobank cohort data) and clinical-outcomes
research where raw data cannot leave the secure environment and only
sufficiently aggregated or privacy-safe outputs may be exported.

---

## How to Use

1. Complete **one checklist instance per export event** — a batch of files
   released at the same time for the same purpose counts as one event.
2. Work through Sections 1–4 in order. Each failing check is a blocker; resolve
   it before proceeding.
3. Both the lead analyst and (where required by the DUA) the data custodian must
   sign Section 5 before the export is transmitted.
4. Retain the signed checklist in the project compliance file for the duration of
   the data-retention period specified in the data-use agreement.

---

## Export Event Header

| Field | Value |
|---|---|
| Project / study name | |
| Data-use agreement / ethics reference | |
| Export date | |
| Lead analyst | |
| Files included in this export (list or attach manifest) | |
| Intended recipient(s) | |
| Transmission method | |
| Purpose of export (publication, collaboration, public archive, internal report) | |

---

## Section 1 — Direct Identifier Check

These are absolute blockers. No export may proceed if any item fails.

| Check | Pass | Notes |
|---|---|---|
| No full names of study subjects in any file | | |
| No national identity numbers, social security numbers, or equivalent unique person IDs | | |
| No full dates of birth (day + month + year combined for an individual) | | |
| No postal addresses, GPS coordinates, or home-location data at a resolution below regional level | | |
| No medical record numbers, biobank sample IDs, or other linkage keys that resolve to an individual in the source register | | |
| No photographs or images from which a subject could be identified | | |

**Section 1 outcome:** ☐ All pass — proceed to Section 2   ☐ One or more failures — STOP

---

## Section 2 — Quasi-Identifier and Small-Cell Check

Quasi-identifiers are variables that do not individually identify a person but can
do so in combination. Apply the cell-suppression and aggregation rules specified
in the data-use agreement.

| Check | Pass | Notes |
|---|---|---|
| All age values are in bands (e.g., 5-year groups) or truncated to integer years — not exact dates | | |
| Geographic variables are aggregated to the level permitted by the DUA (e.g., region, not municipality) | | |
| No frequency table cell has a count below the agreed suppression threshold (commonly N < 5) | | |
| Complementary suppression applied: if a small cell is suppressed, adjacent cells that would allow back-calculation are also suppressed | | |
| Rare-disease or rare-exposure cells with N < threshold are collapsed into an "other" or suppressed category | | |
| Combination of variables in the export does not create a unique or near-unique combination for any individual (cross-tabulation risk assessed) | | |

**Section 2 outcome:** ☐ All pass — proceed to Section 3   ☐ One or more failures — STOP and revise output

---

## Section 3 — Scope and Purpose Check

Confirms the export is covered by the approved data-use agreement and analysis
plan.

| Check | Pass | Notes |
|---|---|---|
| Every variable in this export appears in the approved analysis plan and/or the variable lineage document | | |
| The analysis this output describes is within the scope approved by the DUA and IRB/ethics board | | |
| The intended recipient is listed in the DUA as an authorised collaborator, or a DUA amendment covering this recipient has been executed | | |
| The output does not include any variable added after DUA approval without a documented amendment | | |
| Model coefficients or parameters in the export do not allow reconstruction of individual-level data (e.g., overfitted model with N = 1 cells) | | |
| If the output is a trained model: membership-inference risk has been assessed and is acceptable under the project's threat model | | |

**Section 3 outcome:** ☐ All pass — proceed to Section 4   ☐ One or more failures — STOP

---

## Section 4 — Technical and Format Check

Confirms that the files themselves are clean before transmission.

| Check | Pass | Notes |
|---|---|---|
| Files contain no embedded metadata (author fields, file paths, tracked changes) that reveal infrastructure details or subject information | | |
| Intermediate or working files (raw-data extracts, de-identification mapping tables, log files with record-level details) are excluded from the export | | |
| File names do not contain subject IDs, dates of birth, or other identifiers | | |
| Compressed archives (.zip, .tar) do not contain raw-data files beyond the approved scope | | |
| Code or scripts included in the export do not hard-code credentials, API keys, or internal system paths | | |
| Output file sizes are consistent with aggregate results (unexpectedly large files may indicate inclusion of raw data) | | |

**Section 4 outcome:** ☐ All pass — proceed to Section 5   ☐ One or more failures — STOP and revise

---

## Section 5 — Sign-Off

All four sections must show "All pass" before signing.

**Lead analyst attestation**

I confirm that I have reviewed the files listed in the Export Event Header against
each checklist item above and that, to the best of my knowledge, the export does
not exceed the scope of the approved data-use agreement and does not create an
unreasonable risk of re-identification.

Signed: ________________________________  Date: __________

**Data custodian / governance contact sign-off** *(if required by the DUA)*

I confirm that the output has been reviewed and is approved for release under the
terms of the data-use agreement.

Signed: ________________________________  Date: __________  Role: __________

---

## Section 6 — Transmission Log

Complete after the export is sent.

| Field | Value |
|---|---|
| Actual transmission date and time | |
| Transmission method and platform | |
| Confirmation of receipt (reference number or acknowledgement) | |
| Retention location of signed checklist | |

---

## Amendment and Incident Log

| Date | Event type (amendment / incident / query) | Description | Resolution |
|---|---|---|---|
| | | | |

---

## References

- UK Biobank Output Review Policy (Data Access Agreement Appendix)
- Statistics Sweden (SCB) — Microdata output checking guidelines
- HIPAA Safe Harbor de-identification standard (45 CFR § 164.514(b))
- GDPR Article 5(1)(c) — Data Minimisation; Recital 26 — Anonymisation
- NIST SP 800-188 — De-Identification of Government Datasets
- NIST Privacy Framework Core — CT.DM-P6 (data transmission controls)
- ISO 27001 Annex A.8.12 — Data leakage prevention
