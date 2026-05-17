"""
Unit tests for dp-llm-training/dp_trainer.py and privacy_budget_calculator.py

All tests run without PyTorch or Opacus installed — DPTrainer operates in
mock mode (model=None, optimizer=None), and GaussianMechanism falls back to
the built-in RDP approximation.

Run:
    python -m pytest tests/test_dp_trainer.py -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_DP_DIR = Path(__file__).resolve().parent.parent / "dp-llm-training"
if str(_DP_DIR) not in sys.path:
    sys.path.insert(0, str(_DP_DIR))

from dp_trainer import DPTrainer, GaussianMechanism, PrivacyConfig, PrivacyAccountingRecord  # noqa: E402
from privacy_budget_calculator import compute_plan, sweep_sigma, _rdp_epsilon  # noqa: E402


# ---------------------------------------------------------------------------
# GaussianMechanism
# ---------------------------------------------------------------------------


class TestGaussianMechanism(unittest.TestCase):
    def test_epsilon_positive(self) -> None:
        """Epsilon must be strictly positive for any valid parameters."""
        eps = GaussianMechanism.compute_epsilon(
            noise_multiplier=1.1,
            sample_rate=64 / 5000,
            steps=100,
            delta=1e-5,
        )
        self.assertGreater(eps, 0.0)

    def test_more_steps_more_epsilon(self) -> None:
        """More training steps must consume more privacy budget."""
        params = dict(noise_multiplier=1.1, sample_rate=64 / 5000, delta=1e-5)
        eps_100 = GaussianMechanism.compute_epsilon(steps=100, **params)
        eps_500 = GaussianMechanism.compute_epsilon(steps=500, **params)
        self.assertGreater(eps_500, eps_100)

    def test_more_noise_less_epsilon(self) -> None:
        """Higher noise multiplier must yield lower epsilon (stronger privacy)."""
        params = dict(sample_rate=64 / 5000, steps=200, delta=1e-5)
        eps_low_noise = GaussianMechanism.compute_epsilon(noise_multiplier=0.5, **params)
        eps_high_noise = GaussianMechanism.compute_epsilon(noise_multiplier=2.0, **params)
        self.assertGreater(eps_low_noise, eps_high_noise)

    def test_smaller_delta_larger_epsilon(self) -> None:
        """Tighter delta requirement (smaller δ) must increase epsilon."""
        params = dict(noise_multiplier=1.1, sample_rate=64 / 5000, steps=200)
        eps_loose = GaussianMechanism.compute_epsilon(delta=1e-3, **params)
        eps_tight = GaussianMechanism.compute_epsilon(delta=1e-8, **params)
        self.assertGreater(eps_tight, eps_loose)

    def test_zero_steps_zero_epsilon(self) -> None:
        """Zero gradient steps must consume zero privacy budget."""
        eps = GaussianMechanism.compute_epsilon(
            noise_multiplier=1.0, sample_rate=0.01, steps=0, delta=1e-5
        )
        self.assertAlmostEqual(eps, 0.0, places=6)


# ---------------------------------------------------------------------------
# PrivacyAccountingRecord
# ---------------------------------------------------------------------------


class TestPrivacyAccountingRecord(unittest.TestCase):
    def test_initial_state(self) -> None:
        rec = PrivacyAccountingRecord(delta=1e-5)
        self.assertEqual(rec.steps, 0)
        self.assertAlmostEqual(rec.epsilon_spent, 0.0)
        self.assertFalse(rec.budget_exhausted)
        self.assertEqual(rec.history, [])

    def test_update_appends_history(self) -> None:
        rec = PrivacyAccountingRecord(delta=1e-5)
        rec.update(step=1, epsilon=0.1)
        rec.update(step=2, epsilon=0.2)
        self.assertEqual(len(rec.history), 2)
        self.assertAlmostEqual(rec.epsilon_spent, 0.2)
        self.assertEqual(rec.steps, 2)

    def test_summary_keys(self) -> None:
        rec = PrivacyAccountingRecord(delta=1e-5)
        rec.update(step=5, epsilon=1.5)
        summary = rec.summary()
        self.assertIn("steps_trained", summary)
        self.assertIn("epsilon_spent", summary)
        self.assertIn("delta", summary)
        self.assertIn("budget_exhausted", summary)


# ---------------------------------------------------------------------------
# DPTrainer (mock mode — no torch/opacus)
# ---------------------------------------------------------------------------


class TestDPTrainerMockMode(unittest.TestCase):
    def _make_trainer(self, **kwargs) -> DPTrainer:
        config = PrivacyConfig(
            target_epsilon=kwargs.pop("target_epsilon", 3.0),
            target_delta=kwargs.pop("target_delta", 1e-5),
            noise_multiplier=kwargs.pop("noise_multiplier", 1.1),
        )
        return DPTrainer(
            model=None,
            optimizer=None,
            config=config,
            dataset_size=kwargs.get("dataset_size", 5000),
            batch_size=kwargs.get("batch_size", 64),
        )

    def test_step_returns_float(self) -> None:
        trainer = self._make_trainer()
        loss = trainer.step(batch=None)
        self.assertIsInstance(loss, float)

    def test_step_increments_epsilon(self) -> None:
        trainer = self._make_trainer()
        state_before = trainer.privacy_budget_spent()["epsilon_spent"]
        for _ in range(10):
            trainer.step(batch=None)
        state_after = trainer.privacy_budget_spent()["epsilon_spent"]
        self.assertGreater(state_after, state_before)

    def test_should_stop_false_initially(self) -> None:
        """Trainer should not flag stop before any steps are taken."""
        trainer = self._make_trainer(target_epsilon=10.0)
        self.assertFalse(trainer.should_stop())

    def test_budget_exhaustion_stops_training(self) -> None:
        """Trainer with a very tight epsilon budget should exhaust quickly."""
        trainer = self._make_trainer(
            target_epsilon=0.001,
            noise_multiplier=0.1,  # low noise → fast epsilon consumption
            dataset_size=100,
            batch_size=10,
        )
        for _ in range(1000):
            trainer.step(batch=None)
            if trainer.should_stop():
                break
        self.assertTrue(trainer.should_stop())
        summary = trainer.privacy_budget_spent()
        self.assertTrue(summary["budget_exhausted"])

    def test_privacy_budget_summary_structure(self) -> None:
        trainer = self._make_trainer()
        trainer.step(batch=None)
        summary = trainer.privacy_budget_spent()
        for key in ("steps_trained", "epsilon_spent", "delta", "budget_exhausted"):
            self.assertIn(key, summary, msg=f"Missing key: {key}")

    def test_get_noise_multiplier_for_target(self) -> None:
        """get_noise_multiplier_for_target() should return a positive float."""
        trainer = self._make_trainer(dataset_size=10_000, batch_size=128)
        sigma = trainer.get_noise_multiplier_for_target(target_epsilon=3.0, num_epochs=3)
        self.assertGreater(sigma, 0.0)
        self.assertLess(sigma, 100.0)

    def test_higher_target_epsilon_needs_less_noise(self) -> None:
        """Relaxing ε should require a lower (less noisy) σ."""
        trainer = self._make_trainer(dataset_size=10_000, batch_size=128)
        sigma_tight = trainer.get_noise_multiplier_for_target(target_epsilon=1.0, num_epochs=3)
        sigma_loose = trainer.get_noise_multiplier_for_target(target_epsilon=8.0, num_epochs=3)
        self.assertGreater(sigma_tight, sigma_loose)


# ---------------------------------------------------------------------------
# PrivacyBudgetCalculator
# ---------------------------------------------------------------------------


class TestPrivacyBudgetCalculator(unittest.TestCase):
    _BASE = dict(dataset_size=5000, batch_size=64, epochs=3, target_epsilon=3.0, target_delta=1e-5)

    def test_plan_feasible(self) -> None:
        plan = compute_plan(**self._BASE)
        self.assertTrue(plan.feasible)
        self.assertGreater(plan.required_noise_multiplier, 0.0)

    def test_plan_epsilon_within_budget(self) -> None:
        """Epsilon at the returned σ must be ≤ target_epsilon."""
        plan = compute_plan(**self._BASE)
        self.assertLessEqual(plan.epsilon_at_required_sigma, plan.target_epsilon + 1e-4)

    def test_plan_steps_match_formula(self) -> None:
        plan = compute_plan(**self._BASE)
        expected_steps = 3 * (5000 // 64)
        self.assertEqual(plan.steps, expected_steps)

    def test_tight_epsilon_needs_more_noise(self) -> None:
        """Tighter ε target must demand a higher noise multiplier."""
        plan_tight = compute_plan(
            dataset_size=5000, batch_size=64, epochs=3, target_epsilon=1.0, target_delta=1e-5
        )
        plan_loose = compute_plan(
            dataset_size=5000, batch_size=64, epochs=3, target_epsilon=8.0, target_delta=1e-5
        )
        self.assertGreater(
            plan_tight.required_noise_multiplier, plan_loose.required_noise_multiplier
        )

    def test_sweep_returns_correct_count(self) -> None:
        sigmas = [0.5, 1.0, 1.5, 2.0]
        rows = sweep_sigma(
            dataset_size=5000,
            batch_size=64,
            epochs=3,
            target_epsilon=3.0,
            target_delta=1e-5,
            sigma_values=sigmas,
        )
        self.assertEqual(len(rows), len(sigmas))

    def test_sweep_rows_sorted_by_sigma(self) -> None:
        rows = sweep_sigma(
            dataset_size=5000,
            batch_size=64,
            epochs=3,
            target_epsilon=3.0,
            target_delta=1e-5,
        )
        sigmas = [r.noise_multiplier for r in rows]
        self.assertEqual(sigmas, sorted(sigmas))

    def test_sweep_within_budget_flag(self) -> None:
        """Rows with large σ should be within budget; tiny σ should not."""
        rows = sweep_sigma(
            dataset_size=5000,
            batch_size=64,
            epochs=3,
            target_epsilon=3.0,
            target_delta=1e-5,
            sigma_values=[0.1, 3.0],  # 0.1 → huge ε; 3.0 → tiny ε
        )
        self.assertFalse(rows[0].within_budget)  # σ = 0.1
        self.assertTrue(rows[1].within_budget)  # σ = 3.0

    def test_rdp_epsilon_monotone_in_steps(self) -> None:
        params = dict(noise_multiplier=1.1, sample_rate=0.01, delta=1e-5)
        eps_values = [_rdp_epsilon(steps=s, **params) for s in [10, 50, 100, 500]]
        self.assertEqual(eps_values, sorted(eps_values))


if __name__ == "__main__":
    unittest.main()
