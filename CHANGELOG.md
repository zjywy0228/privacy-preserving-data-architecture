# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added a governed data-access control policy template covering data
  classification, role-based permissions, approval workflows, technical
  controls, audit requirements, incident response, and version review.
- Added implementation-oriented threat models for the FHE,
  differential-private training, and LLM-leakage workstreams.
- Added a data-minimized Markdown/HTML report generator for structured
  LLM-leakage assessment results.
- Added a dependency-free SVG privacy-budget visualization tool with a
  logarithmic epsilon axis, target-budget marker, and deterministic rendering.
- Added a Flower-compatible federated FHE transport/coordinator with opaque
  ciphertext handling, authorized-client and round checks, SHA-256 receipt
  records, a TenSEAL CKKS aggregation backend, and a clearly non-cryptographic
  mock backend for continuous integration.

## [0.3.0] - 2026-07-25

June–July 2026 sprint (2026-05-28 – 2026-07-25): 18 pull requests merged
covering a membership-inference reference implementation, architecture decision
records, audit-log schemas, dashboard enhancements, governance templates,
compliance mappings, packaging, and community infrastructure.

### Added

#### Security & privacy modules
- `llm-leakage-assessment/attacks/membership_inference.py` — reference implementation
  of a membership-inference attack (shadow-model and likelihood-ratio variants) for
  benchmarking LLM privacy guarantees (PR #21)

#### Documentation — architecture decision records
- `docs/adr/0001-why-tenseal.md` — ADR justifying TenSEAL (CKKS) for FHE feature
  extraction; covers security level, performance, and Python ecosystem fit (PR #22)
- `docs/adr/0002-why-opacus.md` — ADR justifying Opacus for differentially-private
  LLM fine-tuning; covers Rényi-DP accountant, per-sample gradient clipping (PR #22)
- `docs/adr/0003-why-csv-control-mapping.md` — ADR explaining the CSV-over-JSON
  choice for the NIST control-mapping artefact (PR #22)
- `docs/glossary.md` — privacy-ML glossary for non-specialist readers; defines FHE,
  DP, membership inference, and related terms with NIST anchors (PR #22)
- `docs/papers/references.bib` — BibTeX index for papers cited across the repository
  (Mironov 2017, Zhu et al. 2019, Carlini et al. 2021, and others) (PR #22)

#### Compliance documentation
- `docs/schemas/dp-audit-log.schema.json` — JSON Schema for the DP training and
  leakage-assessment audit-event log; standalone CLI validator included (PR #24)
- `docs/compliance/gdpr-article-mapping.csv` — 22-row GDPR Article 25/32/5/89
  mapping for all three core workstreams (FHE, DP, leakage) (PR #35)

#### Governance templates
- `governance-templates/irb-amendment-template.md` — fill-in template for amending an
  approved IRB protocol to add FHE or DP controls (PR #20)
- `governance-templates/synthetic-data/generate_synthetic_clinical.py` — synthetic
  EHR generator (age, sex, diagnosis, lab values) using Python Faker and NumPy;
  Parquet + CSV output; no real patient data (PR #30)

#### Architecture & notebooks
- `examples/end-to-end-clinical-data-flow.ipynb` — Jupyter notebook tracing synthetic
  EHR data through FHE feature extraction → DP training → leakage assessment in one
  runnable session (PR #29)
- `gallery/` — PNG renders of all Mermaid architecture diagrams for quick inspection
  without a Mermaid renderer (PR #31)

#### Dashboard enhancements
- NIST Explorer tab: full-text search with highlight, column filter, CSV export (PR #26)
- Leakage assessment expandable detail panel with per-test-case breakdown (PR #27)
- Benchmark chart: log-scale toggle, per-vector-size overhead labels, raw-data table (PR #28)

#### Build & packaging
- `pyproject.toml` — PEP 517/518 packaging metadata; `pip install -e .[dev]` works;
  optional extras for FHE and DP dependencies (PR #32)
- `.github/workflows/publish-testpypi.yml` — automated TestPyPI publish on version
  tag; README badge links to TestPyPI release page (PR #32)
- `.github/workflows/release.yml` — validates version tags against
  `pyproject.toml` and creates a GitHub Release with generated notes
- `Makefile` — `make test`, `make lint`, `make fmt`, `make benchmark`, `make demo`
  targets; wraps ruff, mypy, pytest, and example runners (PR #21)
- `.pre-commit-config.yaml` — ruff format + ruff check + mypy + codespell hooks (PR #21)

#### Repository community files
- `CITATIONS-OF-THIS-REPO.md` — structured record of external citations of this
  repository (PR #25)
- `CODE_OF_CONDUCT.md` — Contributor Covenant 2.1 (PR #25)
- `SECURITY.md` — responsible-disclosure policy and supported versions table (PR #25)
- `README.zh-CN.md` — full Mandarin translation of the README (PR #34)

#### CI & tooling
- `tools/validate_control_mapping.py` — CLI linter for the NIST control-mapping CSV;
  validates column schema, minimum row count, and cell-level constraints; integrated
  into the `validate-nist-csv` CI job (PR #33)

### Changed

- README: "What's new in v0.3" callout added; TestPyPI badge and GDPR-mapping link
  added (PR #25, PR #32, PR #34)
- `pyproject.toml`: version bumped to `0.3.0`

### Fixed

- Corrected the venues, author order, volume/issue, pages, and resolvable DOIs
  for the three anchor papers across documentation, BibTeX, the project site,
  and Python module references.
- Added a citation-integrity regression test to prevent the superseded
  venue/DOI combinations from returning.
- `fix/ruff-format-test-dp-trainer`: ruff format and lint failures in
  `tests/test_dp_trainer.py` corrected; import ordering and unused-variable
  suppressions applied (PR #19)
- mypy `python_version` set to `3.12` in CI to resolve numpy 2.x stub incompatibility
  that caused false-positive type errors (PR #30)

### Sprint statistics

| Metric | Value |
|--------|-------|
| Pull requests merged | 18 (PR #18 – #35) |
| Calendar days | 58 (2026-05-28 – 2026-07-25) |
| New / modified files | ~45 |
| NIST control-mapping rows | 40 |
| GDPR mapping rows | 22 |
| BibTeX references | 8 |
| Architecture decision records | 3 |

---

## [0.2.0] - 2026-05-27

Two-week development sprint (2026-05-13 – 2026-05-27): 17 pull requests merged
covering architecture documentation, prototype module examples, compliance
mapping, CI/CD infrastructure, and test coverage.

### Added

#### Architecture patterns
- `architectures/biomedical-reference-architecture.md` — end-to-end privacy-preserving
  biomedical analytics architecture; motivates FHE and differential-privacy layers for
  institutions handling sensitive health data under HIPAA, GDPR, and related frameworks
  (PR #1)
- `architectures/scientific-collaboration-controlled-access.md` — companion pattern for
  large-scale scientific collaborations (HEP, CMS-style infrastructure); four-layer
  governance design with FAIR-data alignment (PR #15)

#### FHE module
- `fhe-feature-extraction/examples/medical_image_demo.py` — TenSEAL feature extraction
  demo on a publicly downloadable synthetic NIfTI brain-atlas slice; asserts non-trivial
  ciphertext output shape (PR #3)
- `fhe-feature-extraction/benchmarks/run_benchmark.py` — cleartext-vs-ciphertext
  latency and throughput benchmark on synthetic data; results written to
  `benchmarks/results.md` (PR #5)
- Homomorphic-operation correctness fix: projection matrix shape mismatch corrected in
  `fhe_pipeline.py` (PR #11, #16)

#### Differential-privacy module
- `dp-llm-training/examples/text_classification_demo.py` — Opacus + HuggingFace model
  on AG News; logs per-epoch (ε, δ) to stdout (PR #6)
- `dp-llm-training/budget_accountant.py` — `BudgetAccountant` class that tracks
  cumulative (ε, δ) across epochs and emits a JSON audit log at the path set by
  `--audit-log` (PR #6, PR #11)
- `dp-llm-training/dp_calculator_cli.py` — CLI wrapping the Opacus privacy engine
  for one-off budget queries (PR #11)

#### LLM leakage assessment
- `llm-leakage-assessment/assessment_runner.py` — walks the threat taxonomy and
  executes ≥ 15 baseline test cases (prompt injection, log-capture, membership-
  inference probes) against any HuggingFace pipeline or a built-in `MockModel`
  (PR #8)
- `llm-leakage-assessment/threat-taxonomy.md` v2 — 13 threat categories each with a
  mitigation-primitives column and a framework-alignment column; Mermaid threat-
  flow diagram added (PR #12)

#### Governance templates
- `governance-templates/derived-variable-lineage-template.md` — structured YAML
  template for recording transformation lineage from raw variables to model inputs;
  aligned with HIPAA minimum-necessary principle (PR #13)
- `governance-templates/pre-export-output-review-checklist.md` — sign-off checklist
  for pre-publication or inter-institutional output review; references NIST Privacy
  Framework GV.PO-P2 and PPDSA objective 3 (PR #13)

#### Compliance documentation
- `docs/compliance/nist-control-mapping.csv` — 40-row structured mapping from
  architectural patterns to NIST AI RMF, NIST Privacy Framework, and NIST CSF 2.0
  controls (PR #9)
- `docs/compliance/hipaa-ppdsa-alignment.md` — annotated mapping of FHE, DP, and
  leakage-assessment modules to HIPAA Security Rule §164.3xx safeguards and PPDSA
  objectives (PR #10)

#### Validation infrastructure
- `validation/` — FHE and DP validation runners that execute module-level smoke
  tests and emit structured pass/fail JSON; used by the CI coverage gate (PR #11)

#### Dashboard
- `dashboard/` — React + Vite + TypeScript interactive data-exploration dashboard;
  renders module documentation grid, NIST mapping table, benchmark and leakage
  results in-browser (PR #7)
- `dashboard/github-pages/` — static GitHub Pages snapshot with the same content
  (PR #4)

#### Repository hygiene
- `CONTRIBUTING.md` — contribution workflow, AI-assistance policy, and code-quality
  bar (Python ≥ 3.10, ruff, mypy, ≥ 60 % test coverage) (PR #2)
- `CITATION.md` — module-level DOI reference list; cites peer-reviewed papers that
  anchor each privacy-control design decision (PR #2)
- `.github/ISSUE_TEMPLATE/bug_report.md`, `feature_request.md`,
  `pattern_proposal.md` — structured intake templates; the pattern-proposal template
  enforces threat-model and federal-alignment fields (PR #17)
- `.github/PULL_REQUEST_TEMPLATE.md` — standard PR checklist covering lint, type
  hints, test coverage, and PHI-free diff (PR #17)
- `.gitattributes` — enforces LF line endings for all Python and Markdown files (PR #9)
- `.gitignore` — excludes `__pycache__`, `.mypy_cache`, `.coverage`, `.env`, and
  generated benchmark artefacts (PR #9)

### Changed

- README top-level updated to reflect live module status, CI badge, and coverage
  badge after each relevant sprint PR (PRs #2, #9, #14)

### Fixed

- `ruff.toml` syntax corrected from `[tool.ruff]` prefix to standalone format
  required by ruff ≥ 0.4 (PR #9)
- 75 auto-corrected ruff lint errors (unused imports, import ordering, E402 noqa
  placement) across all modules (PR #9, #11)

### CI / Infrastructure

- `.github/workflows/ci.yml` — ruff format + ruff check + mypy + pytest on every
  push and pull request; enforces 65 % coverage threshold on `tests/` (PR #9, #14)
- Coverage reporting via `pytest-cov`; badge sourced from the CI run artefact (PR #14)
- Extended mypy checks on `fhe_pipeline.py`, `dp_trainer.py`, and
  `assessment_runner.py` (PR #14)

### Tests

- Test suite grew from 0 to 68 tests across `tests/test_fhe_pipeline.py`,
  `tests/test_dp_trainer.py`, and `tests/test_assessment_runner.py`
- Coverage: **75 %** on core utilities (target was 60 %) (PR #5, #6, #8, #16)

### Sprint statistics

| Metric | Value |
|--------|-------|
| Pull requests merged | 17 |
| Calendar days | 15 (2026-05-13 – 2026-05-27) |
| New / modified files | ~60 |
| Test cases | 68 |
| Code coverage (core) | 75 % |
| NIST control-mapping rows | 40 |
| Architecture patterns documented | 2 |
| Compliance alignment documents | 2 |

---

## [0.1.0] - 2026-05-12

Initial public release.

### Added

- `fhe-feature-extraction/fhe_pipeline.py` — FHE feature-extraction pipeline using
  TenSEAL; supports CKKS scheme for real-valued medical-imaging features
- `dp-llm-training/dp_trainer.py` — differentially-private LLM fine-tuning wrapper
  using Opacus; exposes `train()` with configurable (ε, δ, max_grad_norm)
- `llm-leakage-assessment/` — threat taxonomy and initial leakage-risk assessment
  scaffolding
- `governance-templates/` — initial access-control and data-handling template stubs
- `docs/compliance/` — initial compliance documentation stubs
- `DEVELOPMENT_PLAN.md` — 2-week sprint roadmap with daily branch/PR schedule
- `README.md`, `LICENSE` (MIT)

[Unreleased]: https://github.com/zjywy0228/privacy-preserving-data-architecture/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/zjywy0228/privacy-preserving-data-architecture/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/zjywy0228/privacy-preserving-data-architecture/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/zjywy0228/privacy-preserving-data-architecture/releases/tag/v0.1.0
