"""
Standalone Privacy Budget Accountant for Differential Privacy Governance

WHY THIS EXISTS:
    DPTrainer provides per-step privacy accounting integrated into the training
    loop. BudgetAccountant exists for a different, complementary purpose:
    governance and audit trail persistence.

    Regulatory and organizational AI-governance frameworks (e.g., NIST AI RMF,
    EU AI Act Article 9, ISO/IEC 42001) increasingly require that privacy claims
    be verifiable after a training run concludes -- not just tracked in-memory
    during training. An auditor must be able to reconstruct, epoch by epoch, how
    much privacy budget was consumed, what the loss was, and whether the formal
    (epsilon, delta)-DP guarantee was maintained throughout.

    BudgetAccountant writes a JSON audit log at any requested path. Each record
    is self-contained: it includes the cumulative epsilon spent at that epoch,
    the fraction of the total budget used, and a boolean flag indicating
    whether the budget was exhausted. This log can be attached to a model card,
    submitted to a compliance review, or loaded back for post-hoc analysis
    without re-running training.

    References:
        NIST AI RMF (2023), Govern 1.7 -- "Processes and procedures are in place
        for the continuous monitoring of AI systems."
        Zhang et al., Neural Processing Letters, 2025 (doi:10.1007/s11063-024-11604-9)
"""

import json
import math
from typing import Dict, Any, List, Optional


# ---------------------------------------------------------------------------
# Minimal RDP-based epsilon computation (self-contained, no Opacus dependency)
# Implements the Mironov 2017 analytical approximation used in dp_trainer.py.
# Duplicated here intentionally to keep BudgetAccountant importable without
# installing the full dp-llm-training package or its torch/opacus dependencies.
# ---------------------------------------------------------------------------

def _compute_epsilon_rdp(
    noise_multiplier: float,
    sample_rate: float,
    steps: int,
    delta: float,
    orders: Optional[List[int]] = None,
) -> float:
    """
    Estimate epsilon after `steps` DP gradient updates (Mironov 2017 RDP bound).

    Args:
        noise_multiplier: Ratio of Gaussian noise std to gradient clip norm.
        sample_rate:      Batch size / dataset size.
        steps:            Total number of gradient update steps so far.
        delta:            Target delta for (epsilon, delta)-DP.
        orders:           RDP orders to evaluate; defaults to a useful range.

    Returns:
        Estimated epsilon under (epsilon, delta)-DP.
    """
    if orders is None:
        orders = list(range(2, 64)) + [128, 256, 512]

    best_eps = float("inf")
    for alpha in orders:
        log_moment = steps * sample_rate ** 2 * alpha / (2.0 * noise_multiplier ** 2)
        eps_candidate = log_moment + math.log(1.0 / delta) / (alpha - 1)
        best_eps = min(best_eps, eps_candidate)
    return best_eps


# ---------------------------------------------------------------------------
# BudgetAccountant
# ---------------------------------------------------------------------------

class BudgetAccountant:
    """
    Per-run privacy budget accountant that produces a persistent JSON audit log.

    Each call to record_epoch() computes the cumulative epsilon spent up to that
    point and appends a structured entry to an in-memory log.  Call save_log()
    at any time -- typically at the end of training -- to write that log to disk
    for governance review.

    Args:
        target_epsilon:   Maximum allowable epsilon (privacy budget).
        target_delta:     Target delta for (epsilon, delta)-DP. Typically 1/N.
        noise_multiplier: Gaussian noise scale relative to gradient clip norm.
        sample_rate:      Fraction of dataset sampled per batch (batch_size / N).
    """

    def __init__(
        self,
        target_epsilon: float,
        target_delta: float,
        noise_multiplier: float,
        sample_rate: float,
    ) -> None:
        self.target_epsilon: float = target_epsilon
        self.target_delta: float = target_delta
        self.noise_multiplier: float = noise_multiplier
        self.sample_rate: float = sample_rate

        self._cumulative_steps: int = 0
        self._epsilon_spent: float = 0.0
        self._log: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Core recording interface
    # ------------------------------------------------------------------

    def record_epoch(self, epoch: int, steps_in_epoch: int, loss: float) -> Dict[str, Any]:
        """
        Record privacy cost for one completed training epoch.

        Computes cumulative epsilon over all steps seen so far (including this
        epoch), appends an audit entry to the in-memory log, and returns that
        entry as a dict.

        Args:
            epoch:          Epoch number (1-indexed is conventional).
            steps_in_epoch: Number of gradient update steps in this epoch.
            loss:           Average training loss for this epoch.

        Returns:
            Dict with keys: epoch, cumulative_steps, epsilon_spent, delta,
            loss, budget_fraction, budget_exhausted.
        """
        self._cumulative_steps += steps_in_epoch

        self._epsilon_spent = _compute_epsilon_rdp(
            noise_multiplier=self.noise_multiplier,
            sample_rate=self.sample_rate,
            steps=self._cumulative_steps,
            delta=self.target_delta,
        )

        budget_fraction = min(self._epsilon_spent / self.target_epsilon, 1.0)
        budget_exhausted = self._epsilon_spent >= self.target_epsilon

        entry: Dict[str, Any] = {
            "epoch": epoch,
            "cumulative_steps": self._cumulative_steps,
            "epsilon_spent": round(self._epsilon_spent, 6),
            "delta": self.target_delta,
            "loss": round(loss, 6),
            "budget_fraction": round(budget_fraction, 6),
            "budget_exhausted": budget_exhausted,
        }
        self._log.append(entry)
        return entry

    # ------------------------------------------------------------------
    # Budget status helpers
    # ------------------------------------------------------------------

    def remaining_budget(self) -> float:
        """Return remaining epsilon budget (clamped to 0 when exhausted)."""
        return max(0.0, self.target_epsilon - self._epsilon_spent)

    def summary(self) -> Dict[str, Any]:
        """Return a snapshot of the current accountant state."""
        return {
            "target_epsilon": self.target_epsilon,
            "target_delta": self.target_delta,
            "noise_multiplier": self.noise_multiplier,
            "sample_rate": self.sample_rate,
            "cumulative_steps": self._cumulative_steps,
            "epsilon_spent": round(self._epsilon_spent, 6),
            "remaining_budget": round(self.remaining_budget(), 6),
            "budget_exhausted": self._epsilon_spent >= self.target_epsilon,
            "epochs_recorded": len(self._log),
        }

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save_log(self, path: str) -> None:
        """
        Write the in-memory audit log to a JSON file at `path`.

        The output is a JSON object with a metadata header and a log array.
        Each log element corresponds to one recorded epoch.

        Args:
            path: Filesystem path for the output JSON file.
        """
        payload = {
            "metadata": {
                "target_epsilon": self.target_epsilon,
                "target_delta": self.target_delta,
                "noise_multiplier": self.noise_multiplier,
                "sample_rate": self.sample_rate,
            },
            "log": self._log,
        }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)

    @classmethod
    def load_log(cls, path: str) -> List[Dict[str, Any]]:
        """
        Load and return the epoch log from a previously saved JSON audit file.

        Args:
            path: Path to a JSON file previously written by save_log().

        Returns:
            List of epoch record dicts (the "log" array from the file).
        """
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        return payload["log"]
