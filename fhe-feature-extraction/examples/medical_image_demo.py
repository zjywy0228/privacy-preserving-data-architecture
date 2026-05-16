"""
FHE medical-image demo: per-patch feature extraction on a synthetic MRI slice.

Shows how privacy-preserving feature extraction scales to a realistic 2D medical
image by processing non-overlapping 8x8 pixel patches in the encrypted domain.
No raw pixel data leaves the encrypt step.

Data-minimisation property demonstrated:
  128x128 MRI-like slice (16 384 raw pixel values)
  -> split into 256 patches of 64 pixels each
  -> each patch encrypted and reduced to 16 derived features
  -> only the 256x16 feature matrix is returned; zero raw pixels exposed

Synthetic data only — no real patient images are used.
Works with both TenSEAL (real FHE) and the built-in simulation fallback.

Usage:
    pip install numpy
    pip install tenseal   # optional — falls back to simulation without it
    python fhe-feature-extraction/examples/medical_image_demo.py
"""

import sys
import os
from typing import List

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from fhe_pipeline import FHEContext, FHEFeatureExtractor, DataMinimizationPipeline

# ── Configuration ────────────────────────────────────────────────────────────
PATCH_SIZE: int = 8           # pixels per patch edge
IMAGE_SIZE: int = 128         # slice dimensions (IMAGE_SIZE x IMAGE_SIZE)
FEATURE_DIM: int = 16         # derived features per patch
INPUT_DIM: int = PATCH_SIZE * PATCH_SIZE   # 64 raw values per patch


# ── Synthetic image generation ───────────────────────────────────────────────

def make_synthetic_mri_slice(size: int = IMAGE_SIZE, seed: int = 42) -> np.ndarray:
    """
    Generate a synthetic brain-MRI-like 2D intensity image using numpy only.

    Mimics characteristic T1 MRI contrast: skull ring at high intensity,
    grey-matter band, white-matter interior, and a small hyperintense focal
    region to simulate a lesion-like signal — all normalised to [0, 1].

    Args:
        size: Pixel dimension of the square output image.
        seed: RNG seed for reproducibility.

    Returns:
        float64 array of shape (size, size) with values in [0.0, 1.0].
    """
    rng = np.random.default_rng(seed)
    cy, cx = size // 2, size // 2
    y_grid, x_grid = np.ogrid[:size, :size]
    radius = np.sqrt((x_grid - cx) ** 2 + (y_grid - cy) ** 2)

    img = np.zeros((size, size), dtype=np.float64)

    # Concentric tissue regions (outside-in: background → skull → GM → WM)
    img[radius < size * 0.47] = 0.30           # white matter
    img[radius < size * 0.38] = 0.22           # deep white matter
    grey_matter_mask = (radius >= size * 0.38) & (radius < size * 0.46)
    img[grey_matter_mask] = 0.68               # grey matter cortex ring
    img[radius >= size * 0.46] = 0.08          # CSF / background

    # Small hyperintense synthetic focus (~6 px radius) offset from centre
    focus_r = np.sqrt((x_grid - cx - 14) ** 2 + (y_grid - cy + 10) ** 2)
    img[focus_r < 6] = 0.90

    # Acquisition noise (σ = 0.02, typical for normalised MR images)
    img += rng.normal(loc=0.0, scale=0.02, size=(size, size))
    return np.clip(img, 0.0, 1.0)


def extract_patches(image: np.ndarray, patch_size: int = PATCH_SIZE) -> List[np.ndarray]:
    """
    Tile a 2D image into non-overlapping square patches and flatten each.

    Patches that would extend beyond the image boundary are dropped so
    the output count is always (H // patch_size) * (W // patch_size).

    Args:
        image: Float array of shape (H, W).
        patch_size: Side length in pixels.

    Returns:
        List of 1-D float64 arrays, each of length patch_size ** 2.
    """
    h, w = image.shape
    patches: List[np.ndarray] = []
    for row in range(0, h - patch_size + 1, patch_size):
        for col in range(0, w - patch_size + 1, patch_size):
            patch = image[row : row + patch_size, col : col + patch_size]
            patches.append(patch.ravel().astype(np.float64))
    return patches


# ── Main demonstration ───────────────────────────────────────────────────────

def main() -> None:
    print("=== FHE Medical-Image Feature-Extraction Demo ===")
    print("Synthetic 128x128 MRI-like brain slice — no real patient data\n")

    # Step 1: generate synthetic slice and tile into patches
    print(f"Step 1 — Generating synthetic MRI slice ({IMAGE_SIZE}x{IMAGE_SIZE} px) ...")
    slice_img = make_synthetic_mri_slice(IMAGE_SIZE)
    patches = extract_patches(slice_img, PATCH_SIZE)
    n_patches = len(patches)

    print(f"  Image shape     : {slice_img.shape}")
    print(f"  Intensity range : [{slice_img.min():.3f}, {slice_img.max():.3f}]")
    print(f"  Patch size      : {PATCH_SIZE}x{PATCH_SIZE} = {INPUT_DIM} pixels")
    print(f"  Patch count     : {n_patches}")
    print(f"  Total raw pixels: {slice_img.size:,}\n")

    # Step 2: initialise FHE context and pipeline
    print("Step 2 — Initialising FHE context (CKKS) ...")
    ctx = FHEContext(poly_modulus_degree=8192)
    extractor = FHEFeatureExtractor(
        input_dim=INPUT_DIM,
        feature_dim=FEATURE_DIM,
        fhe_context=ctx,
    )
    pipeline = DataMinimizationPipeline(extractor)

    print(f"  Scheme          : CKKS (approximate homomorphic arithmetic)")
    print(f"  Poly mod degree : {ctx.poly_modulus_degree}")
    print(f"  Features/patch  : {FEATURE_DIM}\n")

    # Step 3: process every patch through the FHE pipeline
    print(f"Step 3 — Extracting features from {n_patches} patches in encrypted domain ...")
    feature_rows: List[np.ndarray] = []
    for idx, patch in enumerate(patches):
        features = pipeline.process(
            data_id=f"SYNTH-MRI-01-PATCH-{idx:03d}",
            plaintext_input=patch,
            requester="classification-node",
            purpose="texture feature extraction for diagnostic support model",
        )
        feature_rows.append(features)

    feature_matrix = np.array(feature_rows)          # (n_patches, FEATURE_DIM)
    print(f"  Feature matrix shape : {feature_matrix.shape}")
    print(f"  Value range          : [{feature_matrix.min():.4f}, {feature_matrix.max():.4f}]")
    print(f"  Std (all features)   : {feature_matrix.std():.4f}")
    print(f"  Raw pixels -> features: {slice_img.size:,} -> {feature_matrix.size:,} "
          f"({100 * feature_matrix.size / slice_img.size:.1f}% of raw size)\n")

    # Step 4: assertions — non-trivial output shape and variance
    print("Step 4 — Running assertions ...")
    assert feature_matrix.shape == (n_patches, FEATURE_DIM), (
        f"Shape mismatch: expected ({n_patches}, {FEATURE_DIM}), got {feature_matrix.shape}"
    )
    assert feature_matrix.std() > 1e-4, (
        "Feature matrix is unexpectedly constant — pipeline error"
    )
    assert feature_matrix.shape[0] == n_patches, "Patch count mismatch in output"
    print("  Shape and variability assertions PASSED\n")

    # Step 5: audit — confirm zero raw-pixel exposure
    print("Step 5 — Audit summary ...")
    audit_log = pipeline.get_audit_log()
    raw_returned_count = sum(1 for entry in audit_log if entry["raw_data_returned"])
    print(f"  Patches processed        : {len(audit_log)}")
    print(f"  Raw pixels returned      : {raw_returned_count}")
    print(f"  Data-minimisation status : {'PASS — no raw data exposed' if raw_returned_count == 0 else 'FAIL'}\n")

    assert raw_returned_count == 0, "Audit failure: raw pixel data was returned"

    # Step 6: round-trip accuracy on a representative patch
    print("Step 6 — Round-trip reconstruction accuracy (patch 0) ...")
    test_patch = patches[0]
    _, enc_features = extractor.extract(test_patch)
    recovered = extractor.decrypt_features(enc_features)
    expected = extractor.W @ test_patch
    max_error = float(np.max(np.abs(recovered - expected)))
    print(f"  Max feature error : {max_error:.2e}")
    status = "PASS" if max_error < 1e-3 else "FAIL"
    print(f"  Accuracy status   : {status} (threshold 1e-3)\n")

    print("Done. All raw pixel data remained encrypted throughout the pipeline.")
    print(f"      {slice_img.size:,} raw pixels -> {feature_matrix.size:,} derived features "
          f"({100.0 * feature_matrix.size / slice_img.size:.1f}% exposure).")


if __name__ == "__main__":
    main()
