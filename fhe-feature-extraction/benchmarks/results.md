# FHE Pipeline Benchmark Results

**Mode**: TenSEAL (real FHE)
**Trials per size**: 10 (after 2 warm-up runs)
**Statistic**: median wall-clock milliseconds
**Source commit**: 8a52c7c
**Generated**: 2026-11-10T00:44:07+00:00

| Vector size | Cleartext median (ms) | Encrypted median (ms) | Overhead | Max abs error |
|-------------|----------------------:|----------------------:|---------:|--------------:|
| 128 | 0.0012 | 284.4717 | 237059.8x | 2.32172e-06 |
| 512 | 0.0020 | 332.2744 | 166137.2x | 4.58395e-06 |
| 2048 | 0.0049 | 431.2113 | 88002.3x | 7.09715e-06 |

> Cleartext: one NumPy matrix-vector product, averaged over 100 repetitions.
> Encrypted: encryption, CKKS dot products, and decryption of the derived features for the same input.
> Regenerate: python fhe-feature-extraction/benchmarks/run_benchmark.py --require-tenseal --split-roles

## Split-role stage timings (median ms)

| Vector size | Encrypt | Evaluate | Decrypt | Total | Feature ciphertext (KB) | Max abs error |
|-------------|--------:|---------:|--------:|------:|------------------------:|--------------:|
| 128 | 5.0608 | 313.3017 | 36.2558 | 352.2512 | 7346.2 | 4.26085e-06 |
| 512 | 5.0583 | 367.1417 | 32.6718 | 407.9320 | 7345.4 | 4.45912e-06 |
| 2048 | 5.1911 | 444.1224 | 35.1593 | 490.7631 | 7346.4 | 9.11609e-06 |

> The evaluator holds only public evaluation keys; see docs/threat-models/fhe-feature-extraction.md.
> Stage timings include ciphertext serialization and result fingerprint checks; context creation and transport are outside the timed region.
> Total is the median of per-trial stage sums; individual stage medians may not sum to it.
