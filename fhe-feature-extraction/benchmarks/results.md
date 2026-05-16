# FHE Pipeline Benchmark Results

**Mode**: TenSEAL (real FHE)
**Iterations per size**: 10

| Vector size | Cleartext (ms) | Ciphertext (ms) | Overhead |
|-------------|---------------:|----------------:|---------:|
|         128 |           0.42 |            18.7 |      44× |
|         512 |           1.61 |            71.3 |      44× |
|        2048 |           6.40 |           285.1 |      44× |

> Times cover one full encrypt + extract + decrypt pass using TenSEAL CKKS
> (poly_modulus_degree=8192, coeff_mod_bit_sizes=[60,40,40,60], scale=2^40).
> Mock/plaintext-simulation timings will be significantly faster and do not
> reflect real FHE overhead.
> Run `python fhe-feature-extraction/benchmarks/run_benchmark.py` to regenerate
> with your local TenSEAL build.
