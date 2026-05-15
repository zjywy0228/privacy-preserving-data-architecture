# fhe-feature-extraction

Privacy-preserving feature extraction using Fully Homomorphic Encryption (CKKS scheme).

## Purpose

Extracts analytically useful features from sensitive medical or biomedical data
**without decrypting the raw input** at any computation step. Only the derived
feature vector is returned; raw data never leaves the encryption boundary.

Addresses the threat model documented in:
- NIST Privacy Framework (GV.PO-P2 — data-minimisation policy)
- NIST AI RMF (GOVERN 6.1 — privacy risk policies)
- CISA AI Data Security Best Practices (controlled feature access)

## Threat model

| Threat | Mitigation |
|---|---|
| Raw sensitive data exposed to analysis node | Input encrypted before leaving data owner |
| Inference from derived features | Feature dimension << input dimension; projection matrix is public |
| Audit gap — who requested what | `DataMinimizationPipeline` maintains an immutable audit log |

## Dependencies

```
pip install numpy
pip install tenseal   # optional — falls back to numpy simulation if absent
```

Python ≥ 3.10 required.

## Quickstart

```python
from fhe_pipeline import FHEContext, FHEFeatureExtractor, DataMinimizationPipeline
import numpy as np

ctx = FHEContext(poly_modulus_degree=8192)
extractor = FHEFeatureExtractor(input_dim=64, feature_dim=16, fhe_context=ctx)
pipeline = DataMinimizationPipeline(extractor)

raw_patch = np.random.default_rng(0).uniform(0, 1, size=(64,))
features = pipeline.process("RECORD-001", raw_patch, "analysis-node", "classification")
# features.shape == (16,) — raw_patch never returned
```

## Examples

| Script | Description |
|---|---|
| `examples/basic_usage.py` | Synthetic 1-D signal through the pipeline |
| `examples/medical_image_demo.py` | Synthetic 128×128 MRI-like slice, patch-by-patch extraction |

Run either with:

```bash
python fhe-feature-extraction/examples/medical_image_demo.py
```

## Federal alignment

| Framework | Control | How this module addresses it |
|---|---|---|
| NIST Privacy Framework | GV.PO-P2 | Data-minimisation by design; only features leave the pipeline |
| NIST AI RMF | GOVERN 6.1 | Audit log on every feature request |
| NIST CSF 2.0 | PR.DS-01 | Data-at-rest and data-in-use protection via encryption |
| CISA AI Data Security | Controlled feature release | Feature-level output replaces raw-data access |

## References

Zhang et al., "Privacy-Preserving Feature Extraction for Medical Images Based on
Fully Homomorphic Encryption," *Applied Sciences*, 2024.
doi:[10.3390/app14062531](https://doi.org/10.3390/app14062531)
