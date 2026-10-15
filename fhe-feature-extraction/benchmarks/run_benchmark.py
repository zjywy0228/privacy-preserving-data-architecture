"""Measure cleartext and encrypted feature extraction on identical synthetic inputs."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

_HERE = Path(__file__).resolve().parent
_FHE_DIR = _HERE.parent
if str(_FHE_DIR) not in sys.path:
    sys.path.insert(0, str(_FHE_DIR))

from fhe_pipeline import TENSEAL_AVAILABLE, FHEContext, FHEFeatureExtractor  # noqa: E402

_REPO_ROOT = _FHE_DIR.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.provenance import build_provenance  # noqa: E402

VECTOR_SIZES = [128, 512, 2048]
ITERATIONS = 10
WARMUP = 2
FEATURE_DIM = 32
CLEARTEXT_REPEATS = 100
PARAMETERS = {
    "poly_modulus_degree": 8192,
    "coeff_mod_bit_sizes": [60, 40, 40, 60],
    "global_scale_bits": 40,
}


def summarize_ms(samples: list[float]) -> dict[str, float]:
    """Summarize timing samples in milliseconds."""
    if not samples:
        raise ValueError("no timing samples")
    return {
        "median": round(statistics.median(samples), 4),
        "mean": round(statistics.fmean(samples), 4),
        "min": round(min(samples), 4),
        "max": round(max(samples), 4),
    }


def make_projection(input_dim: int, feature_dim: int, seed: int) -> np.ndarray:
    """Create a deterministic projection with unit-length rows."""
    projection = np.random.default_rng(seed).standard_normal((feature_dim, input_dim))
    return projection / np.linalg.norm(projection, axis=1, keepdims=True)


def time_cleartext(
    projection: np.ndarray, vector: np.ndarray, repeats: int = CLEARTEXT_REPEATS
) -> float:
    """Return milliseconds per NumPy matrix-vector product."""
    start = time.perf_counter_ns()
    for _ in range(repeats):
        projection @ vector
    return (time.perf_counter_ns() - start) / 1e6 / repeats


def time_encrypted(extractor: FHEFeatureExtractor, vector: np.ndarray) -> tuple[float, np.ndarray]:
    """Time encryption, feature extraction, and derived-feature decryption."""
    start = time.perf_counter_ns()
    _, encrypted = extractor.extract(vector)
    features = extractor.decrypt_features(encrypted)
    elapsed_ms = (time.perf_counter_ns() - start) / 1e6
    return elapsed_ms, np.asarray(features, dtype=np.float64)


def run_benchmark(
    vector_sizes: list[int] = VECTOR_SIZES,
    trials: int = ITERATIONS,
    warmup: int = WARMUP,
    feature_dim: int = FEATURE_DIM,
    seed: int = 0,
    use_tenseal: bool | None = None,
) -> dict[str, Any]:
    """Measure paired cleartext and encrypted passes with recorded provenance."""
    if use_tenseal is None:
        use_tenseal = TENSEAL_AVAILABLE
    if use_tenseal and not TENSEAL_AVAILABLE:
        raise RuntimeError("TenSEAL is required for encrypted timings: pip install -e .[fhe]")
    if trials < 1:
        raise ValueError("trials must be at least 1")
    if warmup < 0:
        raise ValueError("warmup must be non-negative")
    if not vector_sizes or not 0 < feature_dim <= min(vector_sizes):
        raise ValueError("feature_dim must be positive and at most the smallest vector size")
    ctx = FHEContext() if use_tenseal else None
    rows = []
    for size in vector_sizes:
        projection = make_projection(size, feature_dim, seed + size)
        rng = np.random.default_rng(seed + size)
        vectors = [rng.standard_normal(size) for _ in range(warmup + trials)]
        extractor = (
            FHEFeatureExtractor(
                input_dim=size,
                feature_dim=feature_dim,
                fhe_context=ctx,
                projection_matrix=projection,
            )
            if use_tenseal
            else None
        )
        cleartext_samples = []
        encrypted_samples = []
        max_abs_error = 0.0
        for index, vector in enumerate(vectors):
            cleartext_ms = time_cleartext(projection, vector)
            if extractor is not None:
                encrypted_ms, features = time_encrypted(extractor, vector)
            if index < warmup:
                continue
            cleartext_samples.append(cleartext_ms)
            if extractor is not None:
                encrypted_samples.append(encrypted_ms)
                max_abs_error = max(
                    max_abs_error, float(np.max(np.abs(features - projection @ vector)))
                )
        cleartext = summarize_ms(cleartext_samples)
        encrypted = summarize_ms(encrypted_samples) if use_tenseal else None
        rows.append(
            {
                "vector_size": size,
                "feature_dim": feature_dim,
                "trials": trials,
                "cleartext_ms": cleartext,
                "encrypted_ms": encrypted,
                "overhead_median": round(encrypted["median"] / cleartext["median"], 1)
                if encrypted and cleartext["median"] > 0
                else None,
                "max_abs_error": max_abs_error if use_tenseal else None,
            }
        )
    return {
        "schema_version": "2.0",
        "pipeline": "fhe-feature-extraction",
        "mode": "tenseal" if use_tenseal else "mock",
        "scheme": "CKKS (TenSEAL)" if use_tenseal else "none",
        "parameters": PARAMETERS,
        "warmup": warmup,
        "cleartext_repeats": CLEARTEXT_REPEATS,
        "rows": rows,
        "provenance": build_provenance(
            "measured" if use_tenseal else "mock",
            "fhe-feature-extraction/benchmarks/run_benchmark.py",
            seed=seed,
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    """Render the report as a median timing table."""
    real = report["mode"] == "tenseal"
    mode = (
        "TenSEAL (real FHE)"
        if real
        else "mock (TenSEAL not installed; encrypted timings not measured)"
    )
    provenance = report["provenance"]
    commit = provenance["source_commit"]
    lines = [
        "# FHE Pipeline Benchmark Results",
        "",
        f"**Mode**: {mode}",
        f"**Trials per size**: {report['rows'][0]['trials']} (after {report['warmup']} warm-up runs)",
        "**Statistic**: median wall-clock milliseconds",
        f"**Source commit**: {commit[:7] if commit else 'unknown'}",
        f"**Generated**: {provenance['generated_at']}",
        "",
        "| Vector size | Cleartext median (ms) | Encrypted median (ms) | Overhead | Max abs error |",
        "|-------------|----------------------:|----------------------:|---------:|--------------:|",
    ]
    for row in report["rows"]:
        encrypted = f"{row['encrypted_ms']['median']:.4f}" if real else "not measured"
        overhead = f"{row['overhead_median']}x" if row["overhead_median"] is not None else "n/a"
        error = f"{row['max_abs_error']:.6g}" if real else "n/a"
        lines.append(
            f"| {row['vector_size']} | {row['cleartext_ms']['median']:.4f} | {encrypted} | {overhead} | {error} |"
        )
    lines.extend(
        [
            "",
            "> Cleartext: one NumPy matrix-vector product, averaged over 100 repetitions.",
            "> Encrypted: encryption, CKKS dot products, and decryption of the derived features for the same input.",
            "> Regenerate: python fhe-feature-extraction/benchmarks/run_benchmark.py --require-tenseal",
        ]
    )
    return "\n".join(lines)


def to_dashboard(report: dict[str, Any]) -> dict[str, Any]:
    """Convert a real encrypted report to the dashboard data contract."""
    if report["mode"] != "tenseal":
        raise ValueError("dashboard data requires a TenSEAL run")
    provenance = report["provenance"]
    return {
        "run_timestamp": provenance["generated_at"],
        "scheme": report["scheme"],
        "trials": report["rows"][0]["trials"],
        "statistic": "median",
        "platform": provenance["platform"],
        "provenance": provenance,
        "rows": [
            {
                "vector_size": row["vector_size"],
                "cleartext_ms": round(row["cleartext_ms"]["median"], 4),
                "ciphertext_ms": round(row["encrypted_ms"]["median"], 3),
            }
            for row in report["rows"]
        ],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=VECTOR_SIZES)
    parser.add_argument("--trials", type=int, default=ITERATIONS)
    parser.add_argument("--warmup", type=int, default=WARMUP)
    parser.add_argument("--feature-dim", type=int, default=FEATURE_DIM)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--write-dashboard", action="store_true")
    parser.add_argument(
        "--dashboard-path", type=Path, default=_REPO_ROOT / "docs/assets/data/benchmark.json"
    )
    parser.add_argument("--require-tenseal", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Write a benchmark report and optionally refresh measured dashboard data."""
    args = _build_parser().parse_args(argv)
    try:
        report = run_benchmark(
            args.sizes,
            args.trials,
            args.warmup,
            args.feature_dim,
            args.seed,
            use_tenseal=True if args.require_tenseal else None,
        )
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 2
    out_dir = args.output_dir or (
        _HERE if report["mode"] == "tenseal" else _REPO_ROOT / "artifacts/benchmark"
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    markdown = render_markdown(report)
    (out_dir / "benchmark_results.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    (out_dir / "results.md").write_text(markdown + "\n", encoding="utf-8")
    print(markdown)
    if args.write_dashboard:
        if report["mode"] != "tenseal":
            print("dashboard data requires a TenSEAL run", file=sys.stderr)
            return 2
        args.dashboard_path.write_text(
            json.dumps(to_dashboard(report), indent=2) + "\n", encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
