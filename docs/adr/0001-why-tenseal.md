# ADR 0001 -- Use TenSEAL for Fully Homomorphic Encryption

**Status:** Accepted
**Date:** 2026-05-13
**Decider:** Junyi Zhang (@zjywy0228)

---

## Context

The FHE feature-extraction module needs a Python-accessible FHE library that:

1. Supports the CKKS scheme for real-valued vectors -- required for neural-network feature
   extraction, which involves floating-point arithmetic.
2. Has an active maintenance cycle and a documented public API.
3. Installs via `pip` on Linux, macOS, and Windows without custom compilation.
4. Is used in peer-reviewed academic work so the scheme choice can be cited.

**Candidates evaluated:** Microsoft SEAL (C++ only), PySEAL (unmaintained Python wrapper for
SEAL), HElib (C++), Concrete ML (Zama), TenSEAL.

---

## Decision

Use **TenSEAL** (Microsoft Research / OpenMined; Apache 2.0 license).

### Reasons

1. **CKKS first-class support.** TenSEAL exposes CKKS with batching (SIMD slots), which maps
   naturally to the feature-vector operations needed for biomedical-image analysis.

2. **Pythonic API.** `tenseal.context()`, `tenseal.ckks_vector()`, and element-wise encrypted
   arithmetic work without writing C++ wrappers or maintaining FFI bindings.

3. **pip-installable.** Pre-built wheels are published for Python 3.8-3.12 on the major
   platforms; no compiler toolchain required.

4. **Academic provenance.** TenSEAL is described in: Benaissa et al., "TenSEAL: A Library for
   Encrypted Tensor Operations Using Homomorphic Encryption," ICLR 2021 PPML Workshop.
   DOI: [10.48550/arXiv.2104.03152](https://doi.org/10.48550/arXiv.2104.03152)

5. **Anchoring paper alignment.** The FHE medical-imaging paper that motivates this module
   (DOI: [10.3390/app14062531](https://doi.org/10.3390/app14062531)) uses CKKS-based feature
   extraction; TenSEAL is the most direct Python implementation of that approach.

---

## Alternatives Not Chosen

| Library | Reason rejected |
|---|---|
| Microsoft SEAL | C++ only; no Python API without third-party wrappers |
| PySEAL | Last commit 2019; Python 3.6 only; unmaintained |
| HElib | C++ only; complex installation; no pip wheel |
| Concrete ML | Higher-level compilation approach; less transparent for architecture demonstration |
| HE-Transformer (Intel nGraph) | Archived; no longer maintained |

---

## Consequences

**Positive:**
- Module ships with a single `pip install tenseal` dependency; examples run on commodity
  hardware without GPUs or specialised infrastructure.
- The CKKS scheme's approximate-arithmetic model maps directly to the biomedical-imaging
  use case described in the anchoring paper.

**Negative:**
- TenSEAL does not implement the latest post-quantum parameter recommendations.  It is a
  prototype/demonstration library, not a production-grade implementation.

**Mitigation:**
- The module README clearly states this is a prototype.  Production deployments should engage a
  cryptography specialist for parameter selection, security auditing, and post-quantum
  readiness review.
