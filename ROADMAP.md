# Public Roadmap

Last updated: 2026-08-04

This roadmap covers the twelve months following the `v0.4.0` baseline. Dates are
targets, not promises of third-party adoption or access to institutional data.
Every milestone can be completed with public, synthetic, or de-identified inputs.

## Release milestones

| Target date | Release | Planned public output | Completion evidence |
|---|---|---|---|
| 2026-08-04 | `v0.4.1` | Correct the biomedical citation record, document author-role boundaries, publish this forward roadmap, and extend citation regression tests | Tagged release; green continuous integration; citation-integrity test output |
| 2026-11-30 | `v0.5.0` | Improve governance templates and control mappings, including clearer approval, data-minimization, output-review, and evidence-retention fields | Versioned templates; mapping-validation report; changelog and limitations |
| 2027-02-28 | `v0.6.0` | Publish a structured artifact-review process and incorporate technically actionable feedback that can be shared publicly with reviewer permission | Review template; public issue or redacted review summary; documented disposition of feedback |
| 2027-05-31 | `v0.7.0` | Expand reproducible validation, benchmark reporting, and documentation for the FHE, differential-privacy, and LLM-leakage workstreams | Reproducible commands; machine-readable results; benchmark and limitation reports |
| 2027-08-03 | Twelve-month checkpoint | Publish a public dissemination and maintenance report covering releases, tests, feedback incorporated, unresolved limitations, and the next roadmap | Archived release links; public report; refreshed roadmap |

## Workstream commitments

### Versioned releases and validation

- Keep release notes tied to exact commits, tests, benchmark inputs, and known
  limitations.
- Preserve deterministic, synthetic-data validation paths that do not require
  protected health information or institutional credentials.
- Add benchmark-regression checks where results are stable across supported
  environments.

### Governance templates and control mappings

- Improve the governed-access, data-minimization, transformation-lineage, and
  pre-export review templates.
- Keep National Institute of Standards and Technology mappings traceable to
  implemented repository artifacts.
- Publish machine-readable validation results with each material mapping update.

### Expert and practitioner feedback

- Request review of named, versioned artifacts rather than broad endorsement of
  the project.
- Record the reviewer's capacity, artifact version, observations, and suggested
  next step when the reviewer permits public disclosure.
- Incorporate supported changes through ordinary issues, pull requests, or
  redacted review summaries. Feedback does not imply institutional adoption,
  deployment, funding, or access.

### Public dissemination

- Maintain the GitHub Pages dashboard, README files, changelog, citation record,
  and release archive.
- Publish validation and limitation reports in formats that can be reviewed
  without access to private datasets.
- Keep all examples free of real patient data, protected health information,
  employer-confidential material, and institutional credentials.

## Optional depth

The following items remain useful but are not required for the dated milestones:

- streaming FHE processing for large inputs;
- adaptive clipping for differentially private training;
- dependency-security auditing and remediation documentation; and
- a full documentation link and version audit.
