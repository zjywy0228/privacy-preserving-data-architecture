"""
Synthetic Medical Signal Generator

Generates synthetic, normalised signal datasets that mimic the dimensionality
and statistical structure of medical image patches or clinical signal windows,
without using or exposing any real patient data.

Intended use
------------
- Input for run_fhe_validation.py and run_dp_validation.py
- Architecture testing and CI/CD without requiring a real imaging dataset
- Benchmark reproducibility: fixed seeds produce identical arrays

Signal model
------------
Each synthetic "record" is a 1-D vector representing one flattened image patch
or signal window.  The generative model draws from a mixture of Gaussians that
loosely mimics the multi-modal intensity distribution found in clinical data
(e.g., tissue contrast in MRI, peak/baseline patterns in EEG/ECG).  Cohort
labels simulate case/control or multi-group study designs.

No real PHI is used or generated.  Metadata (cohort label, record ID, visit
number) are purely structural placeholders.

Usage
-----
    from validation.synthetic_medical_signal import generate_dataset, save_dataset

    X, y, meta = generate_dataset(n_samples=200, signal_dim=128)
    save_dataset(X, y, meta, output_dir="validation/data")

    # Or run as script:
    python validation/synthetic_medical_signal.py --n-samples 500 --signal-dim 256
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class RecordMeta:
    record_id: str
    cohort: str  # "control" | "case" | "validation"
    visit: int  # 1-based visit number
    signal_dim: int
    label: int  # integer class label (0, 1, ...)


# ---------------------------------------------------------------------------
# Core generator
# ---------------------------------------------------------------------------


def _gaussian_mixture_signal(
    rng: np.random.Generator,
    dim: int,
    n_components: int = 3,
    noise_std: float = 0.05,
) -> np.ndarray:
    """
    Generate one synthetic signal vector from a Gaussian mixture.

    The component means are fixed per-call via the seeded rng so the
    distribution is deterministic for a given seed.
    """
    # Component weights (random draw)
    weights = rng.dirichlet(np.ones(n_components))
    chosen = rng.choice(n_components, p=weights)

    # Component mean: spread over [0.1, 0.9] range of the signal dimension
    offset = (chosen + 1) / (n_components + 1)
    peak_idx = int(dim * offset)

    # Gaussian bump centred at peak_idx
    x = np.arange(dim, dtype=np.float64)
    width = max(dim / (4 * n_components), 2.0)
    signal = np.exp(-0.5 * ((x - peak_idx) / width) ** 2)

    # Add structured noise and a low-frequency baseline drift
    noise = rng.normal(0.0, noise_std, size=dim)
    freq = rng.uniform(0.5, 2.0)
    baseline = 0.05 * np.sin(2 * np.pi * freq * x / dim)
    signal = signal + noise + baseline

    # Min-max normalise to [0, 1]
    lo, hi = signal.min(), signal.max()
    if hi - lo > 1e-9:
        signal = (signal - lo) / (hi - lo)
    else:
        signal = np.zeros(dim)

    return signal.astype(np.float64)


_COHORT_LABELS = ["control", "case", "validation"]
_LABEL_PARAMS: dict[int, dict[str, float]] = {
    0: {"n_components": 2, "noise_std": 0.04},  # control: cleaner signals
    1: {"n_components": 4, "noise_std": 0.08},  # case: more complex pattern
    2: {"n_components": 3, "noise_std": 0.06},  # validation: intermediate
}


def generate_dataset(
    n_samples: int = 200,
    signal_dim: int = 128,
    n_classes: int = 2,
    seed: int = 42,
    visits_per_subject: int = 1,
) -> tuple[np.ndarray, np.ndarray, list[RecordMeta]]:
    """
    Generate a synthetic dataset of medical signal records.

    Parameters
    ----------
    n_samples:
        Total number of signal records.
    signal_dim:
        Dimensionality of each record (e.g., 128, 256, 512, 2048).
    n_classes:
        Number of cohort classes (1–3).
    seed:
        Random seed for reproducibility.
    visits_per_subject:
        Number of visit records per synthetic subject.

    Returns
    -------
    X: np.ndarray, shape (n_samples, signal_dim) — signal matrix
    y: np.ndarray, shape (n_samples,) — integer labels
    meta: list[RecordMeta] — per-record metadata
    """
    if not 1 <= n_classes <= len(_COHORT_LABELS):
        raise ValueError(f"n_classes must be 1–{len(_COHORT_LABELS)}, got {n_classes}")

    rng = np.random.default_rng(seed)
    labels_pool = list(range(n_classes))

    X: list[np.ndarray] = []
    y: list[int] = []
    meta: list[RecordMeta] = []

    n_subjects = max(1, n_samples // visits_per_subject)
    record_idx = 0

    for subj_idx in range(n_subjects):
        label = labels_pool[subj_idx % n_classes]
        cohort = _COHORT_LABELS[label]
        params = _LABEL_PARAMS.get(label, {"n_components": 3, "noise_std": 0.06})

        for visit in range(1, visits_per_subject + 1):
            if record_idx >= n_samples:
                break
            sig = _gaussian_mixture_signal(rng, signal_dim, **params)
            X.append(sig)
            y.append(label)
            meta.append(
                RecordMeta(
                    record_id=f"SYNTH-{subj_idx:05d}-V{visit}",
                    cohort=cohort,
                    visit=visit,
                    signal_dim=signal_dim,
                    label=label,
                )
            )
            record_idx += 1

    # Trim to exactly n_samples (handles n_subjects * visits > n_samples)
    X_arr = np.stack(X[:n_samples])
    y_arr = np.array(y[:n_samples], dtype=np.int64)
    meta = meta[:n_samples]

    return X_arr, y_arr, meta


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------


def save_dataset(
    X: np.ndarray,
    y: np.ndarray,
    meta: list[RecordMeta],
    output_dir: str | os.PathLike = "validation/data",
    prefix: str = "synthetic",
) -> dict[str, str]:
    """
    Save the dataset to disk and return a dict of output file paths.

    Files written:
        <output_dir>/<prefix>_signals.npy   — signal matrix
        <output_dir>/<prefix>_labels.npy    — label vector
        <output_dir>/<prefix>_meta.json     — per-record metadata
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    signals_path = out / f"{prefix}_signals.npy"
    labels_path = out / f"{prefix}_labels.npy"
    meta_path = out / f"{prefix}_meta.json"

    np.save(signals_path, X)
    np.save(labels_path, y)
    with meta_path.open("w", encoding="utf-8") as fh:
        json.dump([asdict(m) for m in meta], fh, indent=2)

    return {
        "signals": str(signals_path),
        "labels": str(labels_path),
        "meta": str(meta_path),
    }


def load_dataset(
    output_dir: str | os.PathLike = "validation/data",
    prefix: str = "synthetic",
) -> tuple[np.ndarray, np.ndarray, list[dict[str, Any]]]:
    """Load a previously saved dataset. Returns (X, y, meta_list)."""
    out = Path(output_dir)
    X = np.load(out / f"{prefix}_signals.npy")
    y = np.load(out / f"{prefix}_labels.npy")
    with (out / f"{prefix}_meta.json").open("r", encoding="utf-8") as fh:
        meta = json.load(fh)
    return X, y, meta


# ---------------------------------------------------------------------------
# Summary statistics
# ---------------------------------------------------------------------------


def describe_dataset(X: np.ndarray, y: np.ndarray) -> dict[str, Any]:
    """Return a summary dict suitable for logging or JSON output."""
    label_counts: dict[str, int] = {}
    for lbl in np.unique(y):
        label_counts[str(int(lbl))] = int((y == lbl).sum())

    return {
        "n_samples": int(X.shape[0]),
        "signal_dim": int(X.shape[1]),
        "n_classes": int(len(np.unique(y))),
        "label_counts": label_counts,
        "value_range": [round(float(X.min()), 6), round(float(X.max()), 6)],
        "mean": round(float(X.mean()), 6),
        "std": round(float(X.std()), 6),
        "any_nan": bool(np.isnan(X).any()),
        "any_inf": bool(np.isinf(X).any()),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="synthetic_medical_signal",
        description="Generate a synthetic medical-signal dataset (no real PHI).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--n-samples", type=int, default=200)
    p.add_argument("--signal-dim", type=int, default=128)
    p.add_argument("--n-classes", type=int, default=2, choices=[1, 2, 3])
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--visits", type=int, default=1, dest="visits_per_subject")
    p.add_argument("--output-dir", type=str, default="validation/data")
    p.add_argument("--prefix", type=str, default="synthetic")
    p.add_argument("--no-save", action="store_true", help="Print summary only; do not write files.")
    return p


def main(argv: list[str] | None = None) -> None:
    args = _build_parser().parse_args(argv)
    X, y, meta = generate_dataset(
        n_samples=args.n_samples,
        signal_dim=args.signal_dim,
        n_classes=args.n_classes,
        seed=args.seed,
        visits_per_subject=args.visits_per_subject,
    )

    desc = describe_dataset(X, y)
    print(json.dumps(desc, indent=2))

    if not args.no_save:
        paths = save_dataset(X, y, meta, output_dir=args.output_dir, prefix=args.prefix)
        for k, v in paths.items():
            print(f"  [✓] {k}: {v}")


if __name__ == "__main__":
    main()
