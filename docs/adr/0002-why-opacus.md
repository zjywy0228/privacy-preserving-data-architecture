# ADR 0002 -- Use Opacus for Differentially-Private LLM Training

**Status:** Accepted
**Date:** 2026-05-13
**Decider:** Junyi Zhang (@zjywy0228)

---

## Context

The DP training module needs a library that wraps PyTorch optimisers with per-sample gradient
clipping and Gaussian noise injection.  Requirements:

1. Works with standard `torch.nn.Module` models and HuggingFace Trainer-compatible patterns.
2. Implements a credible privacy accountant (RDP or PRV) that converts to (epsilon, delta)-DP.
3. Is actively maintained, documented, and pip-installable.
4. Supports per-epoch (epsilon, delta) reporting suitable for governance audit logs.

**Candidates evaluated:** Opacus (Meta AI), TensorFlow Privacy (Google), JAX privacy (Google),
Google DP Library, custom DP-SGD implementation.

---

## Decision

Use **Opacus** (Meta AI Research; Apache 2.0 license).

### Reasons

1. **PyTorch-native.** Works by wrapping `torch.optim.Optimizer` with `DPOptimizer`; requires
   minimal changes to existing PyTorch training loops.

2. **RDP accountant.** Opacus ships a Renyi DP accountant that converts to (epsilon, delta)-DP
   with tight bounds.  The `get_epsilon()` API provides per-epoch reporting with no additional
   bookkeeping.

3. **HuggingFace compatibility.** `GradSampleModule` wraps any `nn.Module`; compatible with
   HuggingFace models after setting `use_cache=False`.

4. **Academic reference.** Yousefpour et al., "Opacus: User-Friendly Differential Privacy
   Library in PyTorch," NeurIPS 2021 PPML Workshop.
   DOI: [10.48550/arXiv.2109.12298](https://doi.org/10.48550/arXiv.2109.12298)

5. **Anchoring paper alignment.** The DP mechanism paper that motivates this module
   (DOI: [10.1007/s11063-024-11604-9](https://doi.org/10.1007/s11063-024-11604-9)) builds on
   DP-SGD; Opacus is the most direct open-source PyTorch implementation of that approach.

---

## Alternatives Not Chosen

| Library | Reason rejected |
|---|---|
| TensorFlow Privacy | TensorFlow ecosystem only; not compatible with the HuggingFace/PyTorch stack |
| Google DP Library | Lower-level; focused on query release, not model training; no direct PyTorch integration |
| JAX privacy | Requires JAX ecosystem; incompatible with existing PyTorch codebase |
| Custom DP-SGD | High implementation risk; subtle bugs in gradient clipping or noise calibration are not obvious from unit tests |

---

## Consequences

**Positive:**
- Per-epoch (epsilon, delta) values are logged to the governance audit trail via
  `budget_accountant.py`, satisfying NIST AI RMF MEASURE-2.10 and NIST Privacy Framework
  CT.PO-P3.
- Opacus integrates with standard PyTorch tooling (DataLoaders, optimisers, schedulers)
  with minimal code changes.

**Negative:**
- Opacus is incompatible with PyTorch modules that use in-place operations or non-standard
  forward passes.  Some HuggingFace attention layers require `use_cache=False` and other
  compatibility adjustments.

**Mitigation:**
- `dp_trainer.py` disables `use_cache` by default and documents known compatibility
  requirements in its module docstring.
