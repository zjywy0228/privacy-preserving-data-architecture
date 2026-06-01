# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/zjywy0228/privacy-preserving-data-architecture/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/zjywy0228/privacy-preserving-data-architecture/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/zjywy0228/privacy-preserving-data-architecture/releases/tag/v0.1.0
