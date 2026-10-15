# FHE Pipeline Benchmark Results

**Mode**: TenSEAL (real FHE)
**Trials per size**: 10 (after 2 warm-up runs)
**Statistic**: median wall-clock milliseconds
**Source commit**: 0080a41
**Generated**: 2026-10-15T01:48:35+00:00

| Vector size | Cleartext median (ms) | Encrypted median (ms) | Overhead | Max abs error |
|-------------|----------------------:|----------------------:|---------:|--------------:|
| 128 | 0.0012 | 321.1254 | 267604.5x | 1.15316e-06 |
| 512 | 0.0030 | 396.0474 | 132015.8x | 4.56954e-06 |
| 2048 | 0.0105 | 653.6348 | 62250.9x | 7.76236e-06 |

> Cleartext: one NumPy matrix-vector product, averaged over 100 repetitions.
> Encrypted: encryption, CKKS dot products, and decryption of the derived features for the same input.
> Regenerate: python fhe-feature-extraction/benchmarks/run_benchmark.py --require-tenseal
