# Scientific Collaboration Controlled-Access Architecture

## Privacy-Preserving Governed-Data Workflows for Large-Scale Scientific Collaborations

**Version:** 1.0  
**Last updated:** 2026-05-23  
**Status:** Initial release — public review

---

## 1. Purpose and Scope

This reference architecture documents a repeatable four-layer design for large-scale scientific collaborations — particle physics experiments, astronomical surveys, genomics consortia, climate-modeling projects — that must share and analyze sensitive or pre-publication scientific data across dozens of institutions and multiple continents while maintaining controlled access, data integrity, and compliance with collaboration-internal governance rules and applicable federal research-infrastructure security requirements.

The architecture is **collaboration-scenario-anchored**: each layer is grounded in the real data-governance constraints encountered by two of the largest experimental physics collaborations currently operating on U.S. federal research infrastructure:

- **STAR Collaboration** — Solenoidal Tracker at the Relativistic Heavy Ion Collider (RHIC), Brookhaven National Laboratory, Upton, New York. A DOE Office of Science user facility; produces petabyte-scale Au+Au and proton-proton collision datasets distributed across institutions globally.
- **CMS Collaboration** — Compact Muon Solenoid, CERN, Geneva, Switzerland. One of the two large LHC detectors; U.S. participation funded primarily by DOE and NSF; data access managed through the Worldwide LHC Computing Grid (WLCG) and Open Science Grid (OSG).

The architecture is designed to be **domain-transferable**: teams managing data-intensive scientific projects in astrophysics, genomics, climate science, or any other field involving multi-institution collaboration over sensitive or controlled-access data can evaluate and adapt it without adopting a specific vendor stack or having access to the original experimental datasets.

---

## 2. The Governing Problem

Both collaborations above face the same four-part constraint that this architecture addresses:

| Constraint | STAR / RHIC context | CMS / LHC context |
|---|---|---|
| **Raw-data restriction** | Detector raw readout (DSTs) is produced and staged at BNL; collaboration agreement governs which institutions may access which data tiers | Tier-0 (CERN) raw data is not widely accessible; Tier-1 and Tier-2 reconstruction outputs are distributed through WLCG under collaboration access policies |
| **Pre-publication embargo** | Physics results, calibration constants, and analysis code are under internal embargo until collaboration-wide sign-off; premature release violates the collaboration MOU | CMS internal results and software are under collaboration review embargo until approved for public presentation; CERN data-access agreements reinforce this |
| **Multi-institution provenance** | ~60 institutions across ~14 countries contribute calibration, simulation, and analysis; each contribution must be attributable and must not reveal other institutions' unreleased work | ~3,000 physicists across ~50 countries; WLCG grid job results must be attributable to specific software versions, calibration constants, and simulation seeds |
| **AI-tool exposure risk** | AI/LLM coding assistants, document summarizers, and analysis helpers are now routinely used within collaboration workflows; these tools can exfiltrate internal calibration constants, pre-publication results, and software architecture details if used without explicit controls | Same risk applies across CMS; external LLM APIs have no visibility into which data is under embargo vs. public — the researcher must control what enters the tool's context |

The architecture below provides a layered response to all four constraints.

---

## 3. Four-Layer Architecture

```
┌───────────────────────────────────────────────────────────────┐
│  LAYER 4: Output Review and Collaboration Sign-Off            │
│  Internal review · spokesperson approval · public release     │
├───────────────────────────────────────────────────────────────┤
│  LAYER 3: Privacy-Preserving Transformation                   │
│  FHE-encrypted observable extraction · DP-bounded aggregate   │
│  outputs · LLM leakage controls for AI-assisted workflows     │
├───────────────────────────────────────────────────────────────┤
│  LAYER 2: Access Control and Collaboration Governance         │
│  Tier-based data access · role matrix · calibration-version   │
│  lock · audit log · data minimization checkpoint              │
├───────────────────────────────────────────────────────────────┤
│  LAYER 1: Data Classification and Embargo Registration        │
│  Source tier classification · embargo status · permitted-use  │
│  scope · cross-institution provenance record                  │
└───────────────────────────────────────────────────────────────┘
                      ↑ Protected source data
             (raw detector readout, calibration constants,
              simulation seeds, pre-publication analysis code
              — never released outside approved scope)
```

---

### Layer 1 — Data Classification and Embargo Registration

**What this layer does:** Before any data asset enters the collaboration's analysis workflow it is classified by data tier, sensitivity category, embargo status, and permitted-use scope. This layer produces a written intake record that persists through the workflow.

**Checklist items:**

- [ ] Identify the data source and its controlling institution (BNL, CERN Tier-0, a Tier-1 site, a member institution's local cluster).
- [ ] Classify by data tier:
  - Raw detector readout (DSTs, RAW files — highest restriction; collaboration-internal only)
  - Reconstructed data (AODs, mini-AODs — restricted to collaboration members under signed MOU)
  - Calibration constants and alignment records (restricted; version-locked before each physics analysis)
  - Simulation samples (collaboration-internal until publication; random seeds are treated as sensitive until results are public)
  - Analysis code and software (version-controlled; repository access governed by collaboration policy)
  - Pre-publication physics results (under embargo until internal review and spokesperson sign-off)
- [ ] Document embargo status: active embargo / internal-review phase / cleared for conference note / cleared for journal publication.
- [ ] Record the permitted-use scope: which physics analysis, which software release, which calibration tag are in scope for this workflow instance.
- [ ] Identify any cross-institutional data movement and confirm the lawful transfer mechanism (WLCG data-access agreement, BNL user agreement, site-to-site transfer protocol).
- [ ] Record the data-retention and deletion schedule (per DOE or NSF data management plan requirements).

**STAR application:**  
Each physics analysis registers a calibration tag (e.g., `SL23d`) and a software library version (e.g., `SL23d_embed`) as the intake record. Raw DSTs are accessed only through BNL computing resources; derived histogram files and ntuples are the permitted output form for off-site analysis. Pre-publication distributions and fit results are embargoed within the Physics Working Group until the analysis passes internal review and the STAR Speakers Committee approves the result for public presentation.

**CMS application:**  
CMS analyses run against specific `GlobalTag` calibration sets registered in the CMS conditions database. Tier-2 site access is governed by the WLCG VO (Virtual Organization) membership; analysis code is registered in CMSSW version control. Physics results must pass the CMS Physics Approval procedure — including internal review notes and Physics Coordinator sign-off — before any public disclosure.

---

### Layer 2 — Access Control and Collaboration Governance

**What this layer does:** Defines who may access which data tier, in what form, for what purpose, and produces an audit log of every significant access event.

**Role matrix (template — adapt to specific collaboration):**

| Role | Data accessible | Permitted operations | Access method | Audit requirement |
|---|---|---|---|---|
| Analysis physicist (member institution) | Tier-1/Tier-2 reconstructed data, collaboration simulation samples, approved calibration tag | Statistical analysis, histogram production, model fitting | WLCG grid job or collaboration computing cluster only | Log job submission, software version, calibration tag |
| Calibration / detector expert | Raw DSTs (specific subsystem), calibration constants for that subsystem | Calibration validation, constant production | On-site or approved remote access only | Log all constant updates with version tag |
| Physics Working Group (PWG) convener | Pre-publication analysis results from group members | Internal review, approval routing | Internal collaboration review system | Log review actions and approval decisions |
| Collaboration spokesperson / review board | Final pre-publication physics results | Approve or reject public release | Internal review system | Log approval decision and timestamp |
| AI / LLM tool | No direct access to embargoed data or pre-publication results | May operate only on public data and non-identifying derived outputs | Restricted API scope; see Layer 3 LLM controls | Full prompt and response log; reviewed by physicist before submission |
| External user (post-publication) | Public data releases (e.g., CERN Open Data, RHIC public datasets) | Read, reproduce, cite | Public repository (no raw-access or calibration write) | No audit required |

**Calibration-version lock:**  
Before any analysis proceeds, the calibration tag and software release must be locked and recorded. Changing the calibration tag mid-analysis invalidates the embargo-management chain and requires re-registration at Layer 1. This maps to the data-minimization checkpoint in the biomedical architecture: only the variables (calibration constants, detector channels) required for the specific analysis step are in scope.

**Audit log schema:**

```json
{
  "event_id": "<uuid>",
  "timestamp": "<ISO-8601>",
  "actor_role": "<role from matrix above>",
  "action": "<JOB_SUBMIT | CONSTANT_UPDATE | RESULT_ACCESS | REVIEW_ACTION | AI_CALL | PUBLIC_RELEASE>",
  "data_scope": "<data tier, calibration tag, software version, analysis name>",
  "embargo_status": "<ACTIVE | INTERNAL_REVIEW | CLEARED_CONFERENCE | CLEARED_PUBLICATION>",
  "output_produced": "<description or null>",
  "review_status": "<PENDING | APPROVED | REJECTED>"
}
```

---

### Layer 3 — Privacy-Preserving Transformation

**What this layer does:** Applies cryptographic or statistical privacy mechanisms to the computation step so that analytical value is extracted while controlled-access data assets — raw detector readout, calibration constants, pre-publication simulation seeds — are not exposed outside their approved scope.

Three mechanisms are available depending on the computation type:

#### 3A. FHE-Encrypted Computation (for observable extraction from raw detector signals)

Use when: the analysis requires computing derived physics observables from raw detector signals, but the raw signals or calibration constants must not leave the controlled environment in a form that reveals internal calibration choices or unreleased detector performance details.

**How it works:** The source signal (raw detector waveform, hit pattern, energy deposit) is encrypted using the CKKS fully homomorphic encryption (FHE) scheme. Observable extraction computations (track reconstruction features, calorimeter cluster energies, kinematic quantities) run on the ciphertext. Only the resulting encrypted feature vector is returned; the analyst decrypts only the derived observable, not the source signal.

This enforces the same boundary that STAR and CMS collaborations enforce operationally — derived observables are shareable; raw readout and calibration constants are not — but makes that boundary cryptographically verifiable rather than purely procedural.

**Module:** `fhe-feature-extraction/fhe_pipeline.py`

```python
from fhe_pipeline import FHEFeaturePipeline

pipeline = FHEFeaturePipeline(poly_modulus_degree=8192)
encrypted_signal = pipeline.encrypt(raw_detector_waveform)   # encrypted at source
observables = pipeline.extract_features(encrypted_signal)    # runs on ciphertext
result = pipeline.decrypt_features(observables)              # only observables returned
# raw_detector_waveform never appears in analyst environment
```

**What the audit log records:** input hash (not input value), encryption scheme and parameter set, observable extraction function name, output dimensionality, calibration tag used.

**STAR relevance:** Time-Projection Chamber (TPC) raw waveforms contain detector-performance signatures that reveal calibration state. FHE-based feature extraction allows kinematic-analysis features (transverse momentum, rapidity, particle ID) to be shared with off-site analysts while the raw waveform and calibration constants remain within the BNL environment.

#### 3B. Differential Privacy — Bounded Aggregation (for combined results across institutions)

Use when: the analysis merges contributions from multiple institutions (partial datasets, simulation samples, systematic-uncertainty estimates) into a combined result, and the combined output must not allow an external observer to reconstruct individual-institution contributions or identify which institution supplied which calibration choice.

**How it works:** The differential privacy (DP) wrapper adds calibrated Gaussian noise to each contributing record before aggregation, guaranteeing a formal (ε, δ)-privacy bound. The accountant tracks cumulative information leakage across all contributing steps.

**Module:** `dp-llm-training/dp_trainer.py` and `dp-llm-training/budget_accountant.py`

```python
from budget_accountant import BudgetAccountant

accountant = BudgetAccountant(
    target_epsilon=2.0,       # privacy budget
    target_delta=1e-6,
    noise_multiplier=1.3,
    sample_rate=0.01,
)

for epoch, (contributions, loss) in enumerate(collaboration_rounds, start=1):
    entry = accountant.record_epoch(
        epoch=epoch,
        steps_in_epoch=len(contributions),
        loss=loss,
    )
    print(f"Epoch {epoch}: ε={entry['epsilon_spent']:.4f}, "
          f"budget used={entry['budget_fraction']:.1%}")
    if entry["budget_exhausted"]:
        break

accountant.save_log("audit/collaboration_round_privacy_log.json")
```

**What the audit log records:** per-epoch (ε, δ) spent, cumulative budget fraction, whether budget was exhausted before the final round.

**STAR / CMS relevance:** When multiple institutions combine systematic-uncertainty estimates or simulation samples from different Monte Carlo generators, the DP-bounded aggregation guarantees that the published combined result does not allow reverse-engineering of which institution contributed which systematic shift or which simulation seed — protecting unpublished institutional work product even after the collaboration's result is public.

#### 3C. LLM Leakage Controls (for AI-assisted collaboration workflows)

Use when: any AI or LLM tool is used within the governed scientific workflow — for example, to assist with analysis code review, documentation drafting, internal report summarization, or results interpretation.

**Risk:** LLM tools used without explicit controls can exfiltrate embargoed collaboration data through prompt contents, retrieval pipelines, log capture, and context carryover. In a scientific collaboration context, this means calibration constants, unreleased physics results, internal review notes, and simulation parameters can leave the collaboration's controlled environment and enter an external AI service's training pipeline or logs.

**Required controls before introducing any LLM tool:**

- [ ] Run the `llm-leakage-assessment/ASSESSMENT-CHECKLIST.md` for the specific tool and workflow step.
- [ ] Confirm the tool operates only on public data or non-identifying derived outputs (no raw detector data, no embargoed results, no pre-publication distributions, no internal review comments).
- [ ] Verify prompt and response logging is captured in the workflow audit log.
- [ ] Confirm no session-to-session context carryover that could transfer in-scope embargoed data outside the approved scope.
- [ ] Obtain Physics Working Group convener sign-off before introducing any LLM tool into an embargoed analysis workflow.

**What this prevents:** A collaboration member using an external LLM to restructure analysis code accidentally pasting a pre-publication invariant-mass distribution into a prompt; or using a summarization tool on an internal review note that contains unreleased systematic-uncertainty values.

**Module:** `llm-leakage-assessment/ASSESSMENT-CHECKLIST.md`

---

### Layer 4 — Output Review and Collaboration Sign-Off

**What this layer does:** Before any result leaves the collaboration's internal environment, it is reviewed against the permitted-use scope defined in Layer 1 and approved by the relevant review body defined in Layer 2.

**Pre-release output checklist:**

- [ ] Confirm output type is within the permitted scope recorded in the Layer 1 intake record (histogram plots, fit results, cross-section values — not raw distributions from restricted data tiers).
- [ ] Confirm output does not contain direct identifiers of individual-institution contributions where those contributions are not yet public.
- [ ] If output is a combined statistical result: verify DP privacy budget was not exceeded; confirm the (ε, δ) parameters appear in the accompanying analysis note.
- [ ] If output is analysis code: verify the code does not embed calibration constants or simulation seeds that are under active embargo.
- [ ] Capture Physics Working Group convener approval in the audit log.
- [ ] Capture spokesperson / review board sign-off for journal-publication-level results.

**Conference note vs. journal publication distinction:**

| Output type | Review required | Embargo lifted |
|---|---|---|
| Internal technical note | PWG convener | Internal only |
| Conference proceeding / poster | PWG convener + Speakers Committee | Conference presentation date |
| Journal publication | Full collaboration review + spokesperson sign-off | Journal publication date |
| Public dataset release (open data) | Data Preservation group + spokesperson | Dataset release date |

---

## 4. Cross-Framework Compliance Mapping

| Control | DOE SC / BNL User Agreement | NSF Large Facilities Policy | NIST CSF 2.0 | NIST AI RMF |
|---|---|---|---|---|
| Layer 1 data classification and embargo registration | BNL Cyber Security Program §3 — data classification | NSF Large Facility Data Management §4 — data asset inventory | Identify (ID.AM) — Asset Management | Map (MAP-1) — AI system categorization |
| Layer 2 role matrix and access control | BNL §4 — access authorization and need-to-know | NSF §6 — access control for sensitive research data | Protect (PR.AA) — Identity Management and Access Control | Govern (GOV-1) — Roles and responsibilities |
| Layer 2 calibration-version lock | BNL Configuration Management §7 | NSF §7 — configuration management for software and data | Protect (PR.PS) — Platform Security | Manage (MNG-2) — Risk response |
| Layer 2 audit log | BNL §5 — audit and accountability | NSF §8 — monitoring and audit | Detect (DE.CM) — Continuous Monitoring | Govern (GOV-4) — Organizational teams |
| Layer 3A FHE computation | BNL §8 — cryptographic protection | NSF §5 — data protection during transmission and processing | Protect (PR.DS) — Data Security | Map (MAP-5) — Privacy risk |
| Layer 3B DP aggregation | BNL §3 — data sensitivity and handling | NSF §9 — statistical disclosure limitation | Protect (PR.DS) — Data Security | Map (MAP-5) — Privacy risk |
| Layer 3C LLM controls | BNL §10 — third-party service security | NSF AI-use guidance (2024) | Protect (PR.PS) — Platform Security | Govern (GOV-6) — Policies for AI use |
| Layer 4 collaboration sign-off | BNL §11 — change control and release authorization | NSF §10 — data release procedures | Respond (RS.CO) — Incident Communication | Manage (MNG-4) — Risk treatment |

Full NIST control mapping: `docs/compliance/nist-control-mapping.md`.

---

## 5. Worked Example — Heavy-Ion Collision Analysis (STAR Collaboration Pattern)

**Scientific question:** Does the collision-energy dependence of net-kaon multiplicity fluctuations show evidence of a QCD critical point?

**Data assets:** STAR Au+Au collision datasets from the Beam Energy Scan II program at RHIC; calibration constants for the TPC and Time-of-Flight (TOF) detector subsystems; Monte Carlo simulation samples (UrQMD, SMASH generators).

**Architecture walkthrough:**

| Layer | What happens |
|---|---|
| **Layer 1 intake** | Intake record registers: BNL software library tag `SL23d`, TOF calibration tag `TOF_BES2_v3`, simulation samples `UrQMD_BES2_set4` (internal embargo active). Permitted scope: net-kaon moment analysis only. No cross-institution raw-data transfer — grid jobs run at BNL. |
| **Layer 2 access control** | Analysis physicist submits CONDOR jobs to BNL computing cluster under RHIC VO membership. Calibration constants accessed read-only; version locked to `TOF_BES2_v3`. Simulation samples accessed under Physics Working Group (PWG) authorization. Audit log records all job IDs, software versions, calibration tags. |
| **Layer 3A FHE** | TPC raw waveforms processed at BNL: FHE-encrypted track candidates passed to physicist's analysis environment; only kinematic features (pT, rapidity, dE/dx, charge) decrypted. Raw waveforms do not leave BNL environment. |
| **Layer 3B DP aggregation** | Moment calculations (mean, variance, skewness of net-kaon distributions) across sub-run intervals aggregated under DP bounds (ε=2.0, δ=1e-6). Final cumulant ratios are DP-bounded; individual sub-run contributions not reconstructable. Budget accountant log archived with analysis note. |
| **Layer 3C LLM controls** | Physicist uses AI coding assistant to refactor histogram-filling code. Before use: LLM assessment checklist run; tool confirmed to operate only on the code file (no calibration constants or embargoed distributions in context). Prompt and response logged. |
| **Layer 4 sign-off** | PWG convener confirms: result is a cumulant-ratio plot with statistical and systematic errors; no raw distributions from restricted data tiers; calibration tag and DP log attached. Speakers Committee approves for conference presentation. Embargo lifted on presentation date. |

---

## 6. Worked Example — Ultra-Peripheral Heavy-Ion Photoproduction (CMS Collaboration Pattern)

**Scientific question:** What is the nuclear modification factor for J/ψ photoproduction in ultra-peripheral Pb+Pb collisions at √sNN = 5.02 TeV?

**Data assets:** CMS Run 3 Pb+Pb Ultra-Peripheral Collision (UPC) dataset; CMS GlobalTag calibration set `140X_dataRun3_HLT_v3`; STARLIGHT Monte Carlo simulation samples; preliminary fit results under internal review.

**Architecture walkthrough:**

| Layer | What happens |
|---|---|
| **Layer 1 intake** | Intake record registers: CMS dataset `/PbPbUPC/Run2023_v2/AOD`, GlobalTag `140X_dataRun3_HLT_v3`, simulation `STARLIGHT_UPC_PbPb_v2` (internal embargo active; pre-approval for CMS Paper). Permitted scope: J/ψ → e+e− channel differential cross-section only. WLCG Tier-2 access under CMS VO. |
| **Layer 2 access control** | Physicist runs CRAB jobs at WLCG Tier-2 site under CMS VO authorization. GlobalTag is locked; no write access to CMS conditions database. Preliminary fit plots stored in CMS internal results server (restricted access). Audit log captures CRAB task ID, CMSSW version, GlobalTag, access timestamp. |
| **Layer 3A FHE** | CMS calorimeter (ECAL) crystal energy deposits for J/ψ → e+e− candidates encrypted using FHE pipeline; differential cross-section feature extraction runs on ciphertext. Only kinematic features (pT, rapidity, invariant mass) decrypted in physicist's environment. Raw ECAL crystal-level information does not leave CERN Tier-0 environment. |
| **Layer 3B DP aggregation** | Efficiency correction factors contributed by three CMS member institutions aggregated under DP bounds (ε=1.5, δ=1e-6). Published efficiency table represents the DP-bounded combined value; individual-institution correction factors not reverse-engineerable. |
| **Layer 4 sign-off** | CMS Physics Approval procedure: CMS UPC Physics Object Group (POG) review → Physics Coordinator sign-off → CMS Collaboration Board notification. Embargo lifted on journal submission date. Audit log archived in CMS internal JIRA ticket. |

---

## 7. Limitations and Scope

- This document is a reference architecture, not a certification or guarantee of compliance with any specific collaboration MOU, DOE user-facility agreement, or NSF data management plan. Collaboration management, legal counsel, and the relevant computing and software coordinators must be consulted before applying these patterns to real collaboration data.
- FHE performance on detector-scale datasets (gigabytes per event) requires significant optimization beyond the current `fhe_pipeline.py` prototype; the prototype uses CKKS with synthetic signals and includes a mock-fallback mode when TenSEAL is not installed.
- DP epsilon values appropriate for scientific collaboration use cases depend on the number of contributing institutions, the sensitivity of the protected contribution, and the specific aggregation method; the values shown above are illustrative only.
- The LLM controls described in Layer 3C are currently a process-level framework. Cryptographic enforcement (e.g., tool-level sandboxing, API call interception) is a future module.
- This architecture addresses data governance and privacy-preserving computation. Detector calibration methodology, physics analysis techniques, and collaboration policy are outside its scope.

---

## 8. Companion Architecture

This document is a companion to:

| Architecture | Path | Governing context |
|---|---|---|
| Biomedical governed-data workflows | `architectures/biomedical-reference-architecture.md` | HIPAA, EU GDPR Art. 9, Swedish Patientdatalag, IRB |

The two architectures share the same four-layer design and the same three privacy-preserving transformation modules (FHE, DP, LLM controls). The biomedical architecture governs patient-level sensitive records; this architecture governs pre-publication scientific data assets in large international collaborations. The same reusable modules serve both contexts.

---

## 9. Related Resources in This Repository

| Resource | Path | What it adds |
|---|---|---|
| FHE pipeline (Layer 3A) | `fhe-feature-extraction/fhe_pipeline.py` | CKKS implementation for encrypted feature extraction |
| FHE quick-start | `fhe-feature-extraction/examples/basic_usage.py` | Runnable demo on synthetic signal |
| DP trainer (Layer 3B) | `dp-llm-training/dp_trainer.py` | DP training wrapper with RDP privacy accounting |
| Budget accountant (Layer 3B) | `dp-llm-training/budget_accountant.py` | Per-run (ε, δ) audit log for governance review |
| LLM leakage checklist (Layer 3C) | `llm-leakage-assessment/ASSESSMENT-CHECKLIST.md` | 35-item structured assessment for LLM tools on controlled data |
| Derived-variable lineage template (Layer 2) | `governance-templates/derived-variable-lineage-template.md` | Provenance tracking from raw input to published output |
| Pre-export output review checklist (Layer 4) | `governance-templates/pre-export-output-review-checklist.md` | Output-release review for governed workflows |
| NIST control mapping | `docs/compliance/nist-control-mapping.md` | Cross-framework NIST mapping |

---

## 10. Citation

If you use this architecture in your research or institutional implementation, please cite the collaboration-infrastructure papers that grounded its design:

```bibtex
@article{star_netkaon_2021,
  author       = {{STAR Collaboration}},
  title        = {Collision energy dependence of moments of net-kaon multiplicity
                  distributions at RHIC},
  journal      = {Physics Letters B},
  volume       = {785},
  pages        = {551--560},
  year         = {2018},
  doi          = {10.1016/j.physletb.2018.07.066}
}

@article{zhang_dp_llm_2025,
  author       = {Zhang, Junyi and others},
  title        = {A Differential Privacy-Based Mechanism for Preventing Data
                  Leakage in Large Language Model Training},
  journal      = {Neural Processing Letters},
  year         = {2025},
  doi          = {10.1007/s11063-024-11604-9}
}
```

Full BibTeX for all foundation papers in [`CITATION.md`](../CITATION.md).
