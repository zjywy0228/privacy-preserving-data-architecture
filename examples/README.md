# Examples

Runnable demonstrations of the privacy-preserving architecture patterns.
All examples use fully synthetic data — no real PHI, no real credentials.

## End-to-end clinical data-flow notebook

**File:** `end-to-end-clinical-data-flow.ipynb`

A self-contained Jupyter notebook that walks the full architecture pipeline
on a synthetic clinical dataset:

| Stage | Module | What it demonstrates |
|---|---|---|
| 1. Synthetic data generation | NumPy / pandas | 512 synthetic clinical records — reproducible, no PHI |
| 2. FHE feature extraction | `fhe-feature-extraction/fhe_pipeline.py` | Feature extraction in the encrypted domain via CKKS |
| 3. Differentially private training | `dp-llm-training/dp_trainer.py` | Binary classifier with formal (ε, δ) privacy guarantees |
| 4. LLM leakage assessment | `llm-leakage-assessment/assessment_runner.py` | Automated prompt-injection / log-capture / membership-inference test suite |
| 5. End-to-end summary | — | Audit-ready output confirming no PHI exposure at any stage |

**Install dependencies:**
```bash
pip install -r examples/requirements-notebook.txt
```

**Run:**
```bash
jupyter notebook examples/end-to-end-clinical-data-flow.ipynb
# or convert to script:
jupyter nbconvert --to script examples/end-to-end-clinical-data-flow.ipynb
```

**Estimated runtime:** ~3–5 minutes on CPU (TenSEAL FHE dominates).

## Module-specific examples

Each module ships its own focused examples under `<module>/examples/`:

- `fhe-feature-extraction/examples/basic_usage.py` — FHE feature extraction on a synthetic signal
- `fhe-feature-extraction/examples/medical_image_demo.py` — FHE on a synthetic medical-image patch
- `dp-llm-training/examples/` — DP training with budget logging

## Federal alignment

All examples are consistent with:
- NIST AI RMF (GOVERN 1.1, MAP 2.1, MEASURE 2.5)
- NIST Privacy Framework CT.PO-P3, CT.DM-P8
- CISA AI Data Security guidance (2024)
