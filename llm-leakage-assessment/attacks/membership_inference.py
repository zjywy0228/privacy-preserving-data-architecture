"""
Membership-inference attack reference implementation.

Demonstrates why differential-privacy training is necessary: an adversary
with black-box query access can often determine whether a given sample was
in the model's training set by comparing per-sample loss distributions.

References
----------
Shokri et al., "Membership Inference Attacks against Machine Learning
Models," IEEE S&P 2017. DOI: 10.1109/SP.2017.41

Carlini et al., "Membership Inference Attacks From First Principles,"
IEEE S&P 2022. DOI: 10.1109/SP46214.2022.9833649
"""

from __future__ import annotations

import math
import random
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class AttackResult:
    """Summary statistics from a single membership-inference evaluation."""

    accuracy: float
    tpr: float
    fpr: float
    precision: float
    advantage: float

    def __str__(self) -> str:
        return (
            f"accuracy={self.accuracy:.3f}  tpr={self.tpr:.3f}  "
            f"fpr={self.fpr:.3f}  precision={self.precision:.3f}  "
            f"advantage={self.advantage:.3f}"
        )


class LossThresholdAttack:
    """Loss-threshold membership-inference attack (Yeom et al., 2018).

    Why this exists
    ---------------
    Models trained without differential privacy tend to assign measurably
    lower per-sample loss to training records than to held-out records.
    This attack exploits that gap with a single scalar threshold.  The
    *advantage* metric (TPR - FPR) directly measures information leakage:
    a perfectly private model achieves advantage ≈ 0; an unprotected model
    trained to convergence often achieves advantage > 0.2 on small datasets.

    Threat model
    ------------
    Adversary knows:
    - The target sample x.
    - The model's per-sample loss ℓ(x) (query access).
    - The calibration distribution of member / non-member losses (obtained
      from shadow models or a public reference dataset of the same type).

    Adversary does not know:
    - Model weights, training data, or any secret key.
    """

    def __init__(self) -> None:
        self._threshold: float | None = None
        self._fitted: bool = False

    def fit(
        self,
        member_losses: Sequence[float],
        non_member_losses: Sequence[float],
    ) -> LossThresholdAttack:
        """Fit the threshold on a labelled calibration split.

        The threshold that maximises balanced accuracy on the calibration
        set is selected.  The calibration split must be disjoint from the
        evaluation split.
        """
        if not member_losses or not non_member_losses:
            raise ValueError("Both member_losses and non_member_losses must be non-empty.")

        all_losses = list(member_losses) + list(non_member_losses)
        all_labels = [1] * len(member_losses) + [0] * len(non_member_losses)

        best_acc = -1.0
        best_thresh = all_losses[0]

        for t in sorted(set(all_losses)):
            correct = sum(int((loss <= t) == lbl) for loss, lbl in zip(all_losses, all_labels))
            acc = correct / len(all_losses)
            if acc > best_acc:
                best_acc = acc
                best_thresh = t

        self._threshold = best_thresh
        self._fitted = True
        return self

    def predict(self, losses: Sequence[float]) -> list[int]:
        """Return 1 (member) or 0 (non-member) per sample."""
        if not self._fitted or self._threshold is None:
            raise RuntimeError("Call fit() before predict().")
        return [int(loss <= self._threshold) for loss in losses]

    def evaluate(
        self,
        member_losses: Sequence[float],
        non_member_losses: Sequence[float],
    ) -> AttackResult:
        """Evaluate the fitted attack on a held-out split."""
        if not self._fitted or self._threshold is None:
            raise RuntimeError("Call fit() before evaluate().")
        if not member_losses or not non_member_losses:
            raise ValueError("Evaluation sets must be non-empty.")

        t = self._threshold
        tp = sum(1 for loss in member_losses if loss <= t)
        fn = len(member_losses) - tp
        fp = sum(1 for loss in non_member_losses if loss <= t)
        tn = len(non_member_losses) - fp

        total = tp + fn + fp + tn
        accuracy = (tp + tn) / total if total > 0 else 0.0
        tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        advantage = tpr - fpr

        return AttackResult(
            accuracy=accuracy,
            tpr=tpr,
            fpr=fpr,
            precision=precision,
            advantage=advantage,
        )


def simulate_attack(
    *,
    member_mean_loss: float = 0.30,
    member_std_loss: float = 0.10,
    non_member_mean_loss: float = 0.70,
    non_member_std_loss: float = 0.15,
    n_samples: int = 200,
    seed: int = 42,
) -> AttackResult:
    """Simulate a membership-inference scenario without a real model.

    Generates synthetic per-sample losses drawn from normal distributions:
    members have lower mean loss (model has partially memorised them),
    non-members have higher mean loss.  The scenario demonstrates that
    even a moderate loss gap (0.4 nats) gives the attack high advantage
    and motivates DP training to narrow that gap.

    Parameters
    ----------
    member_mean_loss:
        Mean loss for training (member) samples.  Lower → more memorisation.
    member_std_loss:
        Standard deviation of member losses.
    non_member_mean_loss:
        Mean loss for held-out (non-member) samples.
    non_member_std_loss:
        Standard deviation of non-member losses.
    n_samples:
        Number of members *and* non-members to generate (total 2 × n_samples).
    seed:
        Random seed for reproducibility.
    """
    rng = random.Random(seed)

    def _bounded_gauss(mean: float, std: float, n: int) -> list[float]:
        out: list[float] = []
        while len(out) < n:
            v = rng.gauss(mean, std)
            if 0.0 <= v:
                out.append(v)
        return out

    member_losses = _bounded_gauss(member_mean_loss, member_std_loss, n_samples)
    non_member_losses = _bounded_gauss(non_member_mean_loss, non_member_std_loss, n_samples)

    half = n_samples // 2
    attack = LossThresholdAttack()
    attack.fit(member_losses[:half], non_member_losses[:half])
    return attack.evaluate(member_losses[half:], non_member_losses[half:])


def dp_advantage_bound(epsilon: float) -> float:
    """Theoretical upper bound on MIA advantage for a (ε, δ≈0) DP model.

    From Kairouz et al. (2015): advantage ≤ e^ε - 1 ≈ ε for small ε.
    Returns a value in [0, ∞); compare with empirical advantage from
    ``AttackResult.advantage`` to assess how close the model is to the bound.
    """
    if epsilon < 0:
        raise ValueError("epsilon must be non-negative.")
    return math.exp(epsilon) - 1.0
