# 2-Week Development Roadmap

Daily branch + PR schedule. Each day: one branch off `main`, substantive commits, one PR.

Branch naming: `feature/<slug>` · PR title matches slug · merge after review.

---

## Week 1 — Architecture, Setup, Core Modules

### Day 1 · May 12 — Biomedical Reference Architecture
**Branch:** `feature/biomedical-reference-architecture`

- `architectures/README.md` — index of all architecture patterns
- `architectures/biomedical-reference-architecture.md` — full reference architecture for clinical/registry governed-data workflows; data-intake layer, access-control layer, transformation layer, output-review layer; anchored to Nature Aging and Scientific Reports paper patterns

---

### Day 2 · May 13 — Requirements and Project Setup
**Branch:** `feature/project-setup`

- `pyproject.toml` — top-level project metadata
- `fhe-feature-extraction/requirements.txt` — tenseal, numpy, Pillow, scikit-learn
- `dp-llm-training/requirements.txt` — opacus, torch, transformers
- `llm-leakage-assessment/requirements.txt` — openai, anthropic, requests, python-dotenv
- `fhe-feature-extraction/README.md` — module readme with quick-start
- `dp-llm-training/README.md` — module readme with quick-start

---

### Day 3 · May 14 — LLM Assessment Runner (Python)
**Branch:** `feature/assessment-runner`

- `llm-leakage-assessment/assessment_runner.py` — automated tests for:
  - system prompt extraction (known jailbreak prompts)
  - prompt injection via user turn
  - context bleed between sessions
  - RAG retrieval of out-of-scope documents
- `llm-leakage-assessment/test_prompts.json` — curated prompt test vectors
- `llm-leakage-assessment/README.md` — usage guide

---

### Day 4 · May 15 — Deployment Patterns Documentation
**Branch:** `feature/deployment-patterns`

- `docs/deployment-patterns.md` — four concrete deployment pattern templates:
  1. Clinical / pediatric data analytics pipeline
  2. Population-health registry cross-institutional study
  3. LLM-augmented workflow on regulated personal data
  4. Scientific collaboration with pre-publication data governance
- Each pattern: use-case definition, data-sensitivity assumptions, privacy-mechanism selection, validation steps, compliance artifacts

---

### Day 5 · May 16 — Scientific Governed-Access Pattern
**Branch:** `feature/scientific-governed-access`

- `scientific-governed-access/README.md`
- `scientific-governed-access/architecture.md` — controlled-access architecture for large scientific collaborations (STAR/CMS-inspired); raw detector data, derived observables, pre-publication embargo, software provenance
- `scientific-governed-access/ai-tool-leakage-checklist.md` — LLM/AI tool usage checklist for scientific workflows (prompts, code assistants, log exposure)

---

### Day 6 · May 17 — HIPAA and PPDSA Compliance Mapping
**Branch:** `feature/hipaa-ppdsa-compliance`

- `docs/compliance/hipaa-control-mapping.md` — FHE pipeline, DP trainer, LLM checklist mapped to HIPAA Security Rule safeguards (§164.312)
- `docs/compliance/ppdsa-alignment.md` — mapping to National Strategy to Advance Privacy-Preserving Data Sharing and Analytics (PPDSA) pillars: standards, tools, pilots, repositories, benchmarking

---

### Day 7 · May 18 — Interactive Web UI: Assessment Checklist
**Branch:** `feature/ui-assessment-checklist`

- `ui/index.html` — single-page interactive LLM leakage assessment checklist
- `ui/style.css` — clean research-project styling
- `ui/checklist.js` — per-item PASS/FAIL/N/A toggle, progress bar, exportable summary JSON
- `ui/README.md` — how to open locally and deploy to GitHub Pages

---

## Week 2 — Validation, CI, Notebooks, Visualization, GitHub Pages

### Day 8 · May 19 — Synthetic Data Validation Scripts
**Branch:** `feature/synthetic-validation`

- `validation/README.md`
- `validation/synthetic_medical_signal.py` — generates synthetic normalised signal datasets in the dimensionality of medical image patches; no real patient data
- `validation/run_fhe_validation.py` — runs FHE pipeline on synthetic signals, reports round-trip error and throughput
- `validation/run_dp_validation.py` — runs DP trainer on synthetic dataset, reports epsilon/accuracy tradeoff at several noise multiplier values
- `validation/validation-report-template.md` — template for documenting results

---

### Day 9 · May 20 — GitHub Actions CI
**Branch:** `feature/github-actions-ci`

- `.github/workflows/ci.yml` — runs on push/PR: Python 3.10, install deps, run tests
- `tests/__init__.py`
- `tests/test_fhe_pipeline.py` — unit tests: encryption round-trip, feature dimensionality, data-minimization audit log
- `tests/test_dp_trainer.py` — unit tests: privacy accounting, budget exhaustion, noise-multiplier calculation
- `tests/test_assessment_runner.py` — unit tests: checklist structure, section coverage

---

### Day 10 · May 21 — Jupyter Notebook Walkthroughs
**Branch:** `feature/jupyter-notebooks`

- `notebooks/README.md`
- `notebooks/01_fhe_feature_extraction.ipynb` — step-by-step: CKKS context setup, encrypt a synthetic medical signal, extract features, decrypt, measure accuracy; explanatory prose throughout
- `notebooks/02_dp_llm_training.ipynb` — step-by-step: configure DP trainer, run mock training loop, plot epsilon vs steps, show budget exhaustion; links to the DP LLM paper

---

### Day 11 · May 22 — DP Parameter Tuning Tool
**Branch:** `feature/dp-parameter-tuning`

- `dp-llm-training/privacy_budget_calculator.py` — CLI tool: given dataset size, batch size, epochs, and target epsilon, compute required noise multiplier; also prints a sensitivity table (epsilon vs noise_multiplier at fixed steps)
- `dp-llm-training/epsilon_tradeoff_demo.py` — plots accuracy-privacy tradeoff curve on synthetic classification task
- Update `dp-llm-training/README.md` with calculator usage

---

### Day 12 · May 23 — Governance Template Suite (Code)
**Branch:** `feature/governance-templates-suite`

- `governance-templates/access-control-template.md` — role/access matrix template for research teams; columns: role, permitted datasets, permitted operations, access method, audit requirement
- `governance-templates/transformation-log-template.md` — per-pipeline-step log schema: input format, transformation, output format, data elements retained
- `governance-templates/output-review-checklist.md` — pre-release output review for aggregate statistics and model outputs derived from sensitive data
- `governance-templates/incident-response-template.md` — LLM data-exposure incident response playbook

---

### Day 13 · May 24 — Interactive Threat Taxonomy Visualization
**Branch:** `feature/ui-threat-taxonomy`

- `ui/threat-taxonomy.html` — interactive threat tree using vanilla JS + CSS; click a node to expand attack vector, example, mitigation; all data from `llm-leakage-assessment/threat-taxonomy.md`
- `ui/threat-data.js` — threat taxonomy as a JS data structure
- Update `ui/index.html` navigation to link to threat taxonomy view

---

### Day 14 · May 25 — GitHub Pages Landing Page
**Branch:** `feature/github-pages`

- `docs/index.md` — project landing page (renders as GitHub Pages site)
- `docs/_config.yml` — Jekyll config: title, description, theme (minima)
- `docs/papers.md` — research paper cards with abstracts and DOI links
- `docs/architecture.md` — architecture overview for non-technical readers (plain English, diagrams via Mermaid)
- Enable GitHub Pages in repo settings (Settings → Pages → source: `docs/` branch: `main`)

---

## PR Merge Strategy

- Each PR targets `main`
- Squash-merge to keep history clean
- PR description should include: what was added, why it belongs in this project, which paper or exhibit it extends

## After Week 2

- Add Wang, Hu, Zhuang, Liang, Ye as collaborators or ask them to star / open issues
- Write a short technical blog post or preprint describing the architecture suite
- Tag `v0.1.0` release after Day 14 merge
