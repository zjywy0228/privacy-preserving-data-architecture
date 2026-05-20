# Derived-Variable Lineage Template

A structured template for documenting how each analysis variable is derived from
source data in controlled-access biomedical and scientific research environments.
Fills the gap between a data-use agreement (which describes what data may be
accessed) and the analysis code (which describes what happens to it): this
document captures *why* each transformation was made, so a governance reviewer
can confirm that the analysis never exceeds the approved scope.

Modeled on population-registry and clinical-outcome study workflows where raw
source data lives in a nationally administered secure environment (e.g., national
patient registries, biobank cohorts) and derived variables are the only artefacts
that leave that environment.

---

## How to Use This Template

1. Complete one row in the **Variable Registry** table for every variable that
   appears in any analysis script or exported output.
2. For complex transformations, expand the row into a **Variable Detail Block**
   (see Section 2).
3. Review and sign the **Lineage Attestation** (Section 3) before the first
   export of results.
4. Attach this document to the data-use agreement compliance file and update it
   whenever the analysis plan changes.

---

## 1. Variable Registry

| Variable name | Role | Source register / table | Source field(s) | Transformation | Privacy class | Approved in DUA? | Analyst |
|---|---|---|---|---|---|---|---|
| `age_at_diagnosis_y` | Covariate | National patient registry | `dob`, `first_diagnosis_date` | `(first_diagnosis_date − dob) / 365.25`; truncated to integer years | De-identified derived | Yes | |
| `followup_days` | Outcome window | National patient registry | `cohort_entry_date`, `event_date` or `censoring_date` | `min(event_date, censoring_date) − cohort_entry_date` | De-identified derived | Yes | |
| `exposure_flag` | Exposure indicator | Hospital discharge register | `diagnosis_code`, `admission_date` | 1 if any ICD code in approved code list within look-back window, else 0 | De-identified derived | Yes | |
| `comorbidity_score` | Confounder | National patient registry | Multiple ICD fields | Elixhauser / Charlson algorithm on approved comorbidity list | De-identified derived | Yes | |
| `sex_binary` | Stratifier | National patient registry | `sex_code` | Map registry sex code to `{0, 1}`; suppress if cell N < threshold | Quasi-identifier | Yes | |
| `region_code_masked` | Geographic control | National patient registry | `county_code` | Aggregate to ≥5 counties per geographic group; keep only if N ≥ threshold | Quasi-identifier | Confirm | |
| `outcome_event` | Primary outcome | National patient registry | `diagnosis_code`, `event_date` | 1 if first qualifying ICD code after exposure; 0 otherwise | De-identified derived | Yes | |

> **Role vocabulary:** Exposure, Primary outcome, Secondary outcome, Covariate,
> Confounder, Effect modifier, Stratifier, Administrative (not in analysis model).

> **Privacy class vocabulary:**
> - *Direct identifier* — name, ID number, address, date of birth in full.
>   Must not appear in any exported output.
> - *Quasi-identifier* — age in years, sex, geographic unit. May appear in
>   exports only after cell-suppression or aggregation rules are applied.
> - *De-identified derived* — computed from source fields but not reversible to
>   an individual without the source register. Safe to export after output review.
> - *Sensitive attribute* — clinical or behavioural variable. Check data-use
>   agreement before including in any public output.

---

## 2. Variable Detail Blocks

Use a detail block for any variable whose transformation cannot be summarised in
one table cell, or where the derivation logic is non-obvious to a reviewer who
did not write the code.

### Template

```
### Variable: <variable_name>

**Role:** <role from vocabulary above>

**Source:**
- Register / dataset: <name>
- Table / file: <name>
- Field(s): <comma-separated field names>
- Access date range covered: <e.g., 1997-01-01 to 2023-12-31>

**Derivation logic:**
<Plain-language description of the derivation. Reference the script file and
function name so a reviewer can cross-check.>

**Inclusion / exclusion logic:**
<Conditions under which a record contributes to this variable. Include
look-back window, washout period, or minimum follow-up requirements.>

**Output type:** <integer | float | boolean | categorical>
**Units:** <if numeric>
**Missing value handling:** <coded as, imputed as, or excluded — specify>

**Privacy rationale:**
<Why this derivation is safe under the data-use agreement. For quasi-identifiers,
note which cell-suppression or aggregation rule applies.>

**Analyst sign-off:** ___________________________  Date: __________
```

### Example: `exposure_flag`

```
### Variable: exposure_flag

**Role:** Exposure indicator

**Source:**
- Register / dataset: National hospital discharge register
- Table / file: inpatient_episodes
- Field(s): diagnosis_code (ICD-10), admission_date
- Access date range covered: 2000-01-01 to 2022-12-31

**Derivation logic:**
Set to 1 for any subject with at least one inpatient episode whose primary or
secondary ICD-10 code appears in the pre-specified infection code list
(Appendix A of the analysis plan) and whose admission_date falls within the
5-year look-back window before cohort entry. Set to 0 otherwise.
Script: src/derive_exposure.py :: build_exposure_flag().

**Inclusion / exclusion logic:**
- Include: all subjects with cohort_entry_date ≥ 2005-01-01 (ensures 5-year
  look-back is available within register coverage).
- Exclude: subjects with prevalent outcome before cohort entry (see
  outcome_event derivation).

**Output type:** integer (0 / 1)
**Missing value handling:** Subjects with no inpatient records in the look-back
window are coded 0, not missing.

**Privacy rationale:**
The flag is a binary aggregate of multiple episode records. It cannot be mapped
back to a specific admission date or diagnosis code in an export, so it does not
reveal more than the DUA-approved scope. Confirmed with data custodian on
[DATE].

**Analyst sign-off:** ___________________________  Date: __________
```

---

## 3. Lineage Attestation

Sign before any result file, model output, or summary table leaves the controlled
analysis environment.

| Item | Confirmed | Initials | Date |
|---|---|---|---|
| Every exported variable appears in the Variable Registry above | | | |
| No direct identifier (name, full DOB, ID number) appears in any export | | | |
| Quasi-identifiers comply with the cell-suppression rules in the DUA | | | |
| The derivation logic in this document matches the committed analysis code | | | |
| The approved analysis plan covers all variables listed here | | | |
| Any variable added after DUA approval has a documented amendment reference | | | |

**Lead analyst:** ________________________________  Date: __________

**Data custodian / governance contact (if required):** ________________________________  Date: __________

---

## 4. Amendment Log

Record every change to this document after the initial sign-off.

| Date | Changed by | Change description | DUA amendment ref |
|---|---|---|---|
| | | | |

---

## References

- GDPR Article 5(1)(b) — Purpose Limitation; Article 5(1)(e) — Storage Limitation
- HIPAA Safe Harbor de-identification standard (45 CFR § 164.514(b))
- UK Biobank Data Access Agreement — Output Review requirements
- Statistics Sweden (SCB) microdata output review guidelines
- NIST Privacy Framework Core — CT.DM-P4 (data provenance and lineage)
- NIST SP 800-188 — De-Identification of Government Datasets
