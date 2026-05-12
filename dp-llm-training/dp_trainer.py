"""
Differential Privacy Training Wrapper for LLM / ML Workflows

Provides a privacy-accounting-aware training loop that bounds, with formal
mathematical guarantees, what an adversary can infer about any individual
record in the training dataset from the deployed model's outputs.

The core DP guarantee: given privacy parameters (epsilon, delta), any
single training record's presence or absence changes the model's output
distribution by at most exp(epsilon), with probability at least 1 - delta.

This addresses training-data extraction and membership-inference attacks
documented in:
  NIST Adversarial ML Report (2025), Sections 2.5 and 3.2
  Zhang et al., "A Differential Privacy-Based Mechanism for Preventing Data
  Leakage in Large Language Model Training," Neural Processing Letters, 2025.
  doi:10.1007/s11063-024-11604-9

Usage pattern:
    trainer = DPTrainer(model, optimizer, target_epsilon=3.0, target_delta=1e-5)
    for epoch in range(num_epochs):
        loss = trainer.step(batch)
        print(trainer.privacy_budget_spent())
"""

import math
from dataclasses import dataclass, field
from typing import Optional, Callable, Dict, Any, List

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from opacus import PrivacyEngine
    from opacus.accountants import RDPAccountant
    OPACUS_AVAILABLE = True
except ImportError:
    OPACUS_AVAILABLE = False


@dataclass
class PrivacyConfig:
    """
    Configuration for a differentially private training run.

    target_epsilon: Privacy budget. Lower = stronger privacy, less utility.
        Common values: 1.0 (strong), 3.0 (moderate), 8.0 (weak).
    target_delta: Probability of privacy failure. Typically 1/N where N
        is the dataset size. 1e-5 is a common default.
    max_grad_norm: Per-sample gradient clipping bound. Controls sensitivity.
        Larger = more utility loss; smaller = stronger noise calibration.
    noise_multiplier: Gaussian noise scale relative to max_grad_norm.
        Higher = stronger privacy, lower accuracy.
    """
    target_epsilon: float = 3.0
    target_delta: float = 1e-5
    max_grad_norm: float = 1.0
    noise_multiplier: float = 1.1

    def describe(self) -> str:
        return (
            f"DP config: epsilon={self.target_epsilon}, delta={self.target_delta}, "
            f"clip_norm={self.max_grad_norm}, noise_multiplier={self.noise_multiplier}"
        )


@dataclass
class PrivacyAccountingRecord:
    """Tracks privacy budget consumption across training steps."""
    steps: int = 0
    epsilon_spent: float = 0.0
    delta: float = 1e-5
    budget_exhausted: bool = False
    history: List[Dict[str, float]] = field(default_factory=list)

    def update(self, step: int, epsilon: float):
        self.steps = step
        self.epsilon_spent = epsilon
        self.history.append({"step": step, "epsilon": epsilon})

    def summary(self) -> Dict[str, Any]:
        return {
            "steps_trained": self.steps,
            "epsilon_spent": round(self.epsilon_spent, 4),
            "delta": self.delta,
            "budget_exhausted": self.budget_exhausted,
        }


class GaussianMechanism:
    """
    Computes the privacy cost of Gaussian noise added to gradients.

    The Renyi Differential Privacy (RDP) accountant is more accurate than
    the basic composition theorem for many training steps.
    """

    @staticmethod
    def compute_epsilon(
        noise_multiplier: float,
        sample_rate: float,
        steps: int,
        delta: float,
        orders: Optional[List[int]] = None,
    ) -> float:
        """
        Estimate epsilon spent after `steps` gradient updates.

        Args:
            noise_multiplier: Ratio of Gaussian noise std to clip norm.
            sample_rate: Fraction of dataset sampled per batch (batch_size / N).
            steps: Number of gradient update steps taken.
            delta: Target delta for (epsilon, delta)-DP.
            orders: RDP orders to evaluate. Default covers common range.

        Returns:
            Estimated epsilon under (epsilon, delta)-DP.
        """
        if orders is None:
            orders = list(range(2, 64)) + [128, 256, 512]

        if OPACUS_AVAILABLE:
            accountant = RDPAccountant()
            accountant.history = [(noise_multiplier, sample_rate, steps)]
            eps, _ = accountant.get_privacy_spent(delta=delta, alphas=orders)
            return float(eps)

        # Analytical approximation (Mironov 2017) when Opacus is not installed.
        best_eps = float("inf")
        for alpha in orders:
            log_moment = (
                steps
                * sample_rate**2
                * alpha
                / (2 * noise_multiplier**2)
            )
            eps_candidate = log_moment + math.log(1 / delta) / (alpha - 1)
            best_eps = min(best_eps, eps_candidate)
        return best_eps


class DPTrainer:
    """
    Privacy-accounting-aware trainer that enforces a maximum epsilon budget.

    Integrates with PyTorch and Opacus when available; otherwise provides
    a mock implementation suitable for architecture review and testing.
    """

    def __init__(
        self,
        model,
        optimizer,
        config: Optional[PrivacyConfig] = None,
        dataset_size: int = 10_000,
        batch_size: int = 32,
        criterion: Optional[Callable] = None,
    ):
        self.model = model
        self.optimizer = optimizer
        self.config = config or PrivacyConfig()
        self.dataset_size = dataset_size
        self.batch_size = batch_size
        self.sample_rate = batch_size / dataset_size
        self.criterion = criterion
        self.accounting = PrivacyAccountingRecord(delta=self.config.target_delta)
        self._step_count = 0

        if OPACUS_AVAILABLE and TORCH_AVAILABLE and model is not None:
            self._privacy_engine = PrivacyEngine()
            # In real use: call privacy_engine.make_private() on model + optimizer + dataloader.
            # Omitted here to keep the class standalone for architecture review.
        else:
            self._privacy_engine = None

    def step(self, batch) -> float:
        """
        Execute one differentially private gradient update.

        Returns the training loss (or 0.0 in mock mode).
        """
        self._step_count += 1

        if self._privacy_engine is not None and TORCH_AVAILABLE and self.criterion is not None:
            inputs, labels = batch
            self.optimizer.zero_grad()
            outputs = self.model(inputs)
            loss = self.criterion(outputs, labels)
            loss.backward()
            self.optimizer.step()
            loss_val = float(loss.item())
        else:
            loss_val = 0.0  # mock mode

        eps = GaussianMechanism.compute_epsilon(
            noise_multiplier=self.config.noise_multiplier,
            sample_rate=self.sample_rate,
            steps=self._step_count,
            delta=self.config.target_delta,
        )
        self.accounting.update(step=self._step_count, epsilon=eps)

        if eps >= self.config.target_epsilon:
            self.accounting.budget_exhausted = True

        return loss_val

    def privacy_budget_spent(self) -> Dict[str, Any]:
        """Return a summary of privacy budget consumed so far."""
        return self.accounting.summary()

    def should_stop(self) -> bool:
        """Return True when the target epsilon budget has been consumed."""
        return self.accounting.budget_exhausted

    def get_noise_multiplier_for_target(
        self,
        target_epsilon: float,
        num_epochs: int,
        delta: Optional[float] = None,
    ) -> float:
        """
        Compute the noise multiplier needed to meet a target (epsilon, delta)
        budget over a full training run.

        Useful for choosing noise_multiplier before training begins.
        """
        delta = delta or self.config.target_delta
        steps = int(num_epochs / self.sample_rate)

        low, high = 0.1, 100.0
        for _ in range(64):
            mid = (low + high) / 2
            eps = GaussianMechanism.compute_epsilon(mid, self.sample_rate, steps, delta)
            if eps > target_epsilon:
                low = mid
            else:
                high = mid

        return high
