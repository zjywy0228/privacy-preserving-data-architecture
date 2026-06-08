# Glossary

Definitions for terms used across the architecture patterns, prototype modules, and compliance
documentation in this repository.  Aimed at compliance reviewers and research-software engineers
who may not have a background in both applied cryptography and privacy-preserving machine learning.

---

## Cryptographic Primitives

### Fully Homomorphic Encryption (FHE)
A class of encryption schemes that allow arbitrary computations to be performed directly on
ciphertext — encrypted data — without first decrypting it.  The result, once decrypted, equals
the result of performing the same computation on the plaintext.  FHE enables a computation server
to process sensitive data it never sees in the clear.  This repository uses the **CKKS** scheme
via the TenSEAL library (see [ADR 0001](adr/0001-why-tenseal.md)).

**Key property:** Raw input never leaves the data owner in unencrypted form.

**Module:** `fhe-feature-extraction/fhe_pipeline.py`

### CKKS (Cheon-Kim-Kim-Song) Scheme
An FHE scheme optimised for approximate arithmetic on real-valued vectors.  CKKS is the
scheme of choice for machine-learning workloads because feature extraction and aggregation
involve floating-point arithmetic that tolerates a small, controlled approximation error.

**Reference:** Cheon et al., ASIACRYPT 2017. DOI: [10.1007/978-3-319-70694-8_15](https://doi.org/10.1007/978-3-319-70694-8_15)

### Ciphertext
The output of encrypting a plaintext under a key.  All FHE computations in this repository
operate on ciphertext vectors; no intermediate step produces plaintext on the computation server.

### CKKS Public / Secret Key Pair
In CKKS, the **public key** encrypts data and may be distributed to computation servers; the
**secret key** decrypts results and is held only by the data owner.

---

## Differential Privacy

### Differential Privacy (DP)
A mathematical privacy guarantee: an algorithm *M* satisfies *(epsilon, delta)-differential
privacy* if the probability distribution of its output changes by at most a factor of
*e^epsilon*, plus a catastrophic-failure probability *delta*, when any single record is added to
or removed from the input.  In practice, DP ensures a model does not memorise or reveal any
individual record beyond a calibrated bound.

**Module:** `dp-llm-training/dp_trainer.py`, `dp-llm-training/budget_accountant.py`

**Reference:** Dwork et al., TCC 2006. DOI: [10.1007/11681878_14](https://doi.org/10.1007/11681878_14)

### Privacy Budget (epsilon, delta)
- **epsilon:** The privacy-loss bound.  Smaller epsilon means a stronger privacy guarantee.
  Values epsilon <= 3 are commonly considered strong; epsilon <= 8 may be acceptable for some
  deployments.
- **delta:** The probability that the epsilon bound is violated.  Typically set to 1/(n log n)
  where *n* is the dataset size; must be much smaller than 1/n.

### Renyi Differential Privacy (RDP)
A relaxed but composable variant of DP that allows tighter privacy accounting across multiple
training steps.  Opacus uses an RDP accountant internally and converts the final guarantee to
(epsilon, delta)-DP for reporting (see [ADR 0002](adr/0002-why-opacus.md)).

### Differential Privacy Stochastic Gradient Descent (DP-SGD)
The standard training algorithm for differentially private neural networks.  Each training step:
1. Computes per-sample gradients.
2. Clips each gradient to a maximum L2 norm (the **clipping threshold**).
3. Adds calibrated Gaussian noise before the parameter update.

**Reference:** Abadi et al., CCS 2016. DOI: [10.1145/2976749.2978318](https://doi.org/10.1145/2976749.2978318)

### Gaussian Mechanism
Adds Gaussian noise calibrated to the L2 sensitivity of a query.  The standard deviation is
`sigma = (sensitivity * sqrt(2 * ln(1.25/delta))) / epsilon`.  Used by DP-SGD after gradient
clipping.

---

## LLM Data-Leakage Threats

### Membership Inference Attack (MIA)
An adversarial attack in which an adversary with black-box model access attempts to determine
whether a specific sample was in the training set.  Models trained without DP assign measurably
lower loss to training samples, making this attack practical.

**Mitigated by:** DP training (`dp-llm-training/`).
**Reference implementation:** `llm-leakage-assessment/attacks/membership_inference.py`
**Key reference:** Shokri et al., IEEE S&P 2017. DOI: [10.1109/SP.2017.41](https://doi.org/10.1109/SP.2017.41)

### MIA Advantage
The quantity **TPR minus FPR** (true positive rate minus false positive rate) of a membership
inference classifier.  A perfectly private model has advantage near 0; an unprotected model
trained to convergence often achieves advantage > 0.2 on small datasets.  For a
(epsilon, delta~0)-DP model, the theoretical upper bound on advantage is *e^epsilon - 1*.

### Model Inversion Attack
An attack that reconstructs representative training inputs from model outputs or parameters.
Unlike MIA, the goal is recovering the statistical distribution of training data rather than
identifying a specific sample.

### Prompt Injection
An inference-time attack on LLM systems in which adversarial content in user input causes the
model to disregard its system prompt or safety constraints.  Particularly relevant for systems
that pass sensitive documents (e.g., clinical notes) into the context window via RAG.

**Assessment:** `llm-leakage-assessment/assessment_runner.py` test class `pi_*`

### System Prompt Extraction
An inference-time attack that elicits the model's system prompt by crafting specific user
queries.  System prompts may contain data-handling instructions or indirect PHI.

### RAG (Retrieval-Augmented Generation)
An architecture in which the LLM retrieves relevant documents from a vector store at inference
time and includes them in the context window.  RAG over sensitive document stores (e.g., EHR
notes, clinical trial records) creates a leakage surface because retrieved content appears in
the context.

### Memorisation
The tendency of large language models to reproduce verbatim sequences from training data,
including rare or unique strings (e.g., names, identifiers, medical codes).  DP training reduces
but does not eliminate memorisation; the degree of reduction depends on epsilon.

### Log and Telemetry Leakage
Operational risk: query logs, inference logs, and debug traces that include raw prompts or
responses may inadvertently store sensitive data.  Governed deployments require log-sanitisation
policies.  See `governance-templates/pre-export-output-review-checklist.md`.

---

## Access Control and Governance

### Data Minimisation
The principle that only the minimum data necessary for a specified purpose should be collected,
processed, or shared.  Required under HIPAA (section 164.502(b)) and GDPR Article 5(1)(c).

**Template:** `governance-templates/data-minimization-checklist.md`

### Derived Variable
A computed field (e.g., age group from birth date, Body Mass Index from height and weight) used
in a model or analysis instead of the raw source variable.  Derived variables are typically less
sensitive than raw variables and are the preferred unit for cross-institutional data exchange.

**Template:** `governance-templates/derived-variable-lineage-template.md`

### Controlled Access
An access model in which a raw dataset is held centrally under governance controls (IRB approval,
Data Use Agreement, audit logging) and collaborators receive only derived outputs rather than
individual records.

**Architecture:** `architectures/biomedical-reference-architecture.md`

### IRB (Institutional Review Board)
A committee that reviews proposed research involving human subjects.  IRB approval is a
prerequisite for accessing identifiable health data in the United States.

**Template:** `governance-templates/irb-amendment-template.md`

### DUA (Data Use Agreement)
A contractual instrument that governs how data may be accessed, used, and disclosed.  Required by
HIPAA for limited-dataset transfers and common in biomedical research collaborations.

### FAIR Data Principles
A framework (Findable, Accessible, Interoperable, Reusable) for scientific data management.
Accessible in FAIR does not mean open -- it means accessible under well-defined conditions, which
may include authentication, authorisation, and a DUA.

**Architecture:** `architectures/scientific-collaboration-controlled-access.md`

---

## Regulatory Frameworks

### HIPAA Security Rule
U.S. federal regulation (45 CFR Part 164, Subparts A and C) governing the security of electronic
protected health information (ePHI).  Key provisions relevant to this repository:

| Safeguard | Provision |
|---|---|
| Encryption at rest | section 164.312(a)(2)(iv) |
| Encryption in transit | section 164.312(e)(2)(ii) |
| Audit controls | section 164.312(b) |
| De-identification | section 164.514(b) |

**Mapping:** `docs/compliance/nist-control-mapping.csv`, `docs/compliance/hipaa-control-mapping.md`

### GDPR Article 9
EU General Data Protection Regulation provision that restricts processing of special category
data, including health and genetic data.  Requires explicit consent or a specific legal basis;
cross-border transfers require additional safeguards.

### PPDSA (Privacy-Preserving Data Sharing Architecture)
NIST SP 800-188 (draft), a reference framework for technical and governance approaches to
sharing data without exposing raw records.

**Mapping:** `docs/compliance/ppdsa-alignment.md`

### NIST AI Risk Management Framework (AI RMF)
NIST AI 100-1 (2023).  Organises AI risk management around four functions: Govern, Map, Measure,
Manage.  Control identifiers use the format FUNCTION-N.N (e.g., GOVERN-1.1, MEASURE-2.8).

**Mapping:** `docs/compliance/nist-control-mapping.csv`
**DOI:** [10.6028/NIST.AI.100-1](https://doi.org/10.6028/NIST.AI.100-1)

### NIST Privacy Framework (PF)
NIST Privacy Framework v1.0 (2020).  Organises privacy risk management around five functions:
Identify-P, Govern-P, Control-P, Communicate-P, Protect-P.  Control identifiers follow the
format FN.CT-PN (e.g., PR.PO-P1, CT.PO-P3).

### NIST CSF 2.0
NIST Cybersecurity Framework version 2.0 (2024).  Six functions: Govern, Identify, Protect,
Detect, Respond, Recover.  Control identifiers follow the format FN.CT-NN (e.g., PR.DS-01).

---

## Library Abbreviations

| Abbreviation | Full name | Repository role |
|---|---|---|
| TenSEAL | Tensor-oriented Secure Encrypted Algebra Library | FHE computation (`fhe-feature-extraction/`) |
| Opacus | Meta AI differentially-private training library for PyTorch | DP training (`dp-llm-training/`) |
| HuggingFace (HF) | Hugging Face Transformers / Datasets hub | DP demo model and dataset loader |
| RDP | Renyi Differential Privacy accountant | Privacy budget tracking |
| MIA | Membership Inference Attack | `llm-leakage-assessment/attacks/` |
| PHI | Protected Health Information (HIPAA definition) | Governance templates |
| ePHI | Electronic Protected Health Information | Compliance documentation |
| RAG | Retrieval-Augmented Generation | Threat taxonomy (inference-time leakage) |
| IRB | Institutional Review Board | Governance templates |
| DUA | Data Use Agreement | Governance templates |
| FAIR | Findable, Accessible, Interoperable, Reusable | Scientific architecture pattern |
