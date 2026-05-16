"""
FHE Pipeline Benchmark Runner
==============================
Measures wall-clock time for encrypt + extract + decrypt at three vector sizes
(128, 512, 2048), averaging over 10 iterations each.

Outputs:
  - Markdown table to stdout
  - benchmarks/results.md   (same table, overwritten on each run)
  - benchmarks/benchmark_results.json  (machine-readable, same schema as
    docs/assets/data/benchmark.json)

TenSEAL not required: falls back to mock mode and notes this in output.

Usage:
    python fhe-feature-extraction/benchmarks/run_benchmark.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Dict, List

import numpy as np

# ---------------------------------------------------------------------------
# Resolve the fhe-feature-extraction directory so we can import fhe_pipeline
# regardless of where the script is invoked from.
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent          # …/benchmarks/
_FHE_DIR = _HERE.parent                          # …/fhe-feature-extraction/
if str(_FHE_DIR) not in sys.path:
    sys.path.insert(0, str(_FHE_DIR))

from fhe_pipeline import (  # noqa: E402
    TENSEAL_AVAILABLE,
    FHEContext,
    FHEFeatureExtractor,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
VECTOR_SIZES: List[int] = [128, 512, 2048]
ITERATIONS: int = 10
FEATURE_DIM: int = 32   # fixed output dimension for all runs


# ---------------------------------------------------------------------------
# Core measurement logic
# ---------------------------------------------------------------------------

def _time_one_pass(extractor: FHEFeatureExtractor, vec: np.ndarray) -> float:
    """Return wall-clock seconds for one encrypt+extract+decrypt pass."""
    t0 = time.perf_counter()
    _, enc_features = extractor.extract(vec)
    extractor.decrypt_features(enc_features)
    return time.perf_counter() - t0


def run_benchmark(
    vector_sizes: List[int] = VECTOR_SIZES,
    iterations: int = ITERATIONS,
    feature_dim: int = FEATURE_DIM,
) -> List[Dict]:
    """
    Run the benchmark and return a list of result dicts (one per vector size).

    Each dict has keys:
        vector_size   int
        mean_ms       float   mean wall-clock time in milliseconds
        min_ms        float
        max_ms        float
        iterations    int
        mode          str     "tenseal" | "mock"
    """
    ctx = FHEContext()
    mode = "tenseal" if TENSEAL_AVAILABLE else "mock"
    results: List[Dict] = []

    for size in vector_sizes:
        rng = np.random.default_rng(seed=size)
        extractor = FHEFeatureExtractor(
            input_dim=size,
            feature_dim=feature_dim,
            fhe_context=ctx,
        )

        timings: List[float] = []
        for _ in range(iterations):
            vec = rng.standard_normal(size).astype(np.float64)
            elapsed = _time_one_pass(extractor, vec)
            timings.append(elapsed)

        arr = np.array(timings) * 1_000  # seconds -> ms
        results.append(
            {
                "vector_size": size,
                "mean_ms": round(float(arr.mean()), 3),
                "min_ms": round(float(arr.min()), 3),
                "max_ms": round(float(arr.max()), 3),
                "iterations": iterations,
                "mode": mode,
            }
        )

    return results


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _render_markdown_table(results: List[Dict], mode: str) -> str:
    mode_note = (
        "TenSEAL (real FHE)"
        if mode == "tenseal"
        else "mock/plaintext simulation (TenSEAL not installed)"
    )
    lines: List[str] = [
        "# FHE Pipeline Benchmark Results",
        "",
        f"**Mode**: {mode_note}",
        f"**Iterations per size**: {results[0]['iterations']}",
        "",
        "| Vector size | Mean (ms) | Min (ms) | Max (ms) |",
        "|-------------|----------:|---------:|---------:|",
    ]
    for r in results:
        lines.append(
            f"| {r['vector_size']:>11} | {r['mean_ms']:>9.3f} | {r['min_ms']:>8.3f} | {r['max_ms']:>8.3f} |"
        )
    lines += [
        "",
        "> Times cover one full encrypt + extract + decrypt pass.",
        "> Run `python fhe-feature-extraction/benchmarks/run_benchmark.py` to regenerate.",
    ]
    return "\n".join(lines)


def _render_json(results: List[Dict]) -> str:
    payload = {
        "schema_version": "1.0",
        "pipeline": "fhe-feature-extraction",
        "benchmark": results,
    }
    return json.dumps(payload, indent=2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("Running FHE pipeline benchmark …")
    if not TENSEAL_AVAILABLE:
        print("  [!] TenSEAL not installed — using mock/plaintext mode.\n")

    results = run_benchmark()
    mode = results[0]["mode"]

    table_md = _render_markdown_table(results, mode)
    json_str = _render_json(results)

    # --- stdout ---
    print(table_md)

    # --- write results.md ---
    md_path = _HERE / "results.md"
    md_path.write_text(table_md + "\n", encoding="utf-8")
    print(f"\n[✓] Written: {md_path}")

    # --- write benchmark_results.json ---
    json_path = _HERE / "benchmark_results.json"
    json_path.write_text(json_str + "\n", encoding="utf-8")
    print(f"[✓] Written: {json_path}")


if __name__ == "__main__":
    main()
