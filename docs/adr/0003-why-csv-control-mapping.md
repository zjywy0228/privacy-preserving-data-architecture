# ADR 0003 -- Use CSV for NIST Control Mapping

**Status:** Accepted
**Date:** 2026-05-17
**Decider:** Junyi Zhang (@zjywy0228)

---

## Context

The repository needs a machine-readable format for the mapping between architecture patterns and
controls from the NIST AI RMF, NIST Privacy Framework, NIST CSF 2.0, and HIPAA Security Rule.

**Formats considered:**

| Format | Human-readable | GitHub renders natively | Importable by compliance teams | Authoritative for federal submissions |
|---|---|---|---|---|
| Markdown table | Yes | Yes | No (manual copy) | No |
| CSV | Yes | Yes (sortable table) | Yes (Excel, Sheets) | No |
| JSON | Partial | No (raw text) | Moderate | No |
| YAML | Yes | No (raw text) | No | No |
| OSCAL (JSON/XML) | No | No | No | Yes |

---

## Decision

Use **CSV** (`docs/compliance/nist-control-mapping.csv`) as the primary machine-readable format,
with a Markdown companion (`nist-control-mapping.md`) for GitHub rendering.

### Reasons

1. **Target audience workflow.** Compliance reviewers and auditors typically work in Excel or
   Google Sheets, not JSON viewers or YAML parsers.  A CSV that opens directly without
   conversion reduces friction to zero.

2. **GitHub renders CSV as a sortable table.** GitHub's native CSV renderer shows the file as
   a filterable, column-sortable table without any browser extension.

3. **Appropriate scope.** OSCAL is the correct long-term format for formal federal submissions.
   For a research prototype repository, the overhead of an OSCAL toolchain is disproportionate
   to the benefit at this stage.

4. **Linter-friendly.** A Python script can validate column presence, control-ID format, and
   row completeness against a schema without heavy dependencies (see the `validate-nist-csv`
   CI job in `.github/workflows/ci.yml`).

5. **Precedent.** NIST SP 800-53 itself publishes control catalogues in both OSCAL (XML/JSON)
   and Excel spreadsheet form; the spreadsheet form is the artefact compliance teams actually
   use day-to-day.

---

## Alternatives Not Chosen

| Format | Reason not primary |
|---|---|
| Markdown table only | Not programmatically queryable; sorting requires tooling |
| JSON | Less readable in GitHub UI; higher barrier for direct compliance-team use |
| YAML | Readable but non-standard for tabular data; no native GitHub table renderer |
| OSCAL | Correct for federal submissions; premature for a research prototype |

---

## Consequences

**Positive:**
- Compliance teams can download and sort by control family, pattern, or module in any
  spreadsheet application without tooling.
- The CI `validate-nist-csv` job enforces minimum row count and required column presence on
  every push, preventing accidental schema drift.

**Negative:**
- CSV does not support nested structures.  A pattern mapped to multiple NIST controls requires
  multiple rows rather than an array, increasing row count but also improving filtering.

**Future work:**
- Consider adding an OSCAL-export script (`tools/export_oscal.py`) that converts the CSV to
  an OSCAL Component Definition when the repository reaches a stage requiring formal federal
  attestation.
