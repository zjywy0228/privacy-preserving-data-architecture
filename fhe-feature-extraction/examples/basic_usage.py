"""
Basic usage demo: FHE feature extraction on a synthetic medical signal.

Simulates the data-minimization pattern used in biomedical research:
- Raw patient signal (plaintext) is encrypted immediately on receipt
- Feature extraction runs on the encrypted representation
- Only the derived feature vector is returned; raw data never leaves the encrypt step

No real patient data is used. The synthetic signal mimics the dimensionality
of a flattened 8x8 image patch, representative of a medical imaging sub-region.
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from fhe_pipeline import FHEContext, FHEFeatureExtractor, DataMinimizationPipeline


def generate_synthetic_signal(dim: int = 64, seed: int = 0) -> np.ndarray:
    """Generate a synthetic medical signal for demonstration."""
    rng = np.random.default_rng(seed)
    # Simulate a normalised intensity patch (e.g., MRI sub-region, 0–1 range)
    return rng.uniform(0.1, 0.9, size=(dim,)).astype(np.float64)


def main():
    print("=== FHE Feature Extraction Demo ===\n")

    INPUT_DIM = 64   # 8x8 image patch (flattened)
    FEATURE_DIM = 16  # Compact feature representation

    print("1. Initialising FHE context (CKKS scheme)...")
    ctx = FHEContext(poly_modulus_degree=8192)
    print(f"   Polynomial modulus degree: {ctx.poly_modulus_degree}")
    print(f"   Global scale: 2^{int(np.log2(ctx.global_scale))}\n")

    print("2. Creating feature extractor (linear projection, public weights)...")
    extractor = FHEFeatureExtractor(
        input_dim=INPUT_DIM,
        feature_dim=FEATURE_DIM,
        fhe_context=ctx,
    )
    print(f"   Input dimension: {INPUT_DIM}")
    print(f"   Feature dimension: {FEATURE_DIM}\n")

    print("3. Wrapping in data-minimisation pipeline...")
    pipeline = DataMinimizationPipeline(extractor)

    # Simulate processing 3 de-identified study records
    for i in range(3):
        signal = generate_synthetic_signal(dim=INPUT_DIM, seed=i)
        features = pipeline.process(
            data_id=f"STUDY-RECORD-{i+1:03d}",
            plaintext_input=signal,
            requester="analysis-node-A",
            purpose="feature extraction for downstream classification model",
        )
        print(f"   Record STUDY-RECORD-{i+1:03d}: "
              f"input shape {signal.shape} -> features shape {features.shape}")

    print("\n4. Audit log (raw data was never returned):")
    for entry in pipeline.get_audit_log():
        print(f"   {entry['data_id']} | requester={entry['requester']} | "
              f"raw_data_returned={entry['raw_data_returned']} | "
              f"features_returned={entry['features_returned']}")

    print("\n5. Verifying round-trip accuracy (encrypt -> extract -> decrypt)...")
    test_signal = generate_synthetic_signal(dim=INPUT_DIM, seed=99)
    _, enc_features = extractor.extract(test_signal)
    recovered = extractor.decrypt_features(enc_features)
    expected = extractor.W @ test_signal
    error = np.max(np.abs(recovered - expected))
    print(f"   Max reconstruction error: {error:.6e}")
    print(f"   {'PASS' if error < 1e-3 else 'FAIL'} (threshold 1e-3)\n")

    print("Done. The pipeline extracted features without exposing raw input data.")


if __name__ == "__main__":
    main()
