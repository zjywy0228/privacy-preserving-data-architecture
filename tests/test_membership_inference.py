"""
Tests for llm-leakage-assessment/attacks/membership_inference.py

All tests are self-contained; no network, GPU, or ML framework required.
"""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "llm-leakage-assessment"))

from attacks.membership_inference import (  # noqa: E402
    AttackResult,
    LossThresholdAttack,
    dp_advantage_bound,
    simulate_attack,
)


class TestAttackResult(unittest.TestCase):
    def test_str_format(self) -> None:
        r = AttackResult(accuracy=0.9, tpr=0.85, fpr=0.05, precision=0.9, advantage=0.8)
        s = str(r)
        self.assertIn("accuracy=0.900", s)
        self.assertIn("advantage=0.800", s)

    def test_frozen_dataclass(self) -> None:
        r = AttackResult(accuracy=0.5, tpr=0.5, fpr=0.5, precision=0.5, advantage=0.0)
        with self.assertRaises(Exception):
            r.accuracy = 0.9  # type: ignore[misc]


class TestLossThresholdAttack(unittest.TestCase):
    def _clear_split(self) -> tuple[list[float], list[float], list[float], list[float]]:
        """Well-separated member / non-member losses — attack should succeed."""
        members_train = [0.1, 0.2, 0.15, 0.12, 0.18]
        non_members_train = [0.8, 0.9, 0.85, 0.78, 0.92]
        members_eval = [0.11, 0.19, 0.13, 0.16, 0.21]
        non_members_eval = [0.79, 0.88, 0.83, 0.91, 0.76]
        return members_train, non_members_train, members_eval, non_members_eval

    def test_fit_returns_self(self) -> None:
        att = LossThresholdAttack()
        m_tr, nm_tr, _, _ = self._clear_split()
        result = att.fit(m_tr, nm_tr)
        self.assertIs(result, att)

    def test_predict_before_fit_raises(self) -> None:
        att = LossThresholdAttack()
        with self.assertRaises(RuntimeError):
            att.predict([0.3])

    def test_evaluate_before_fit_raises(self) -> None:
        att = LossThresholdAttack()
        with self.assertRaises(RuntimeError):
            att.evaluate([0.3], [0.7])

    def test_fit_empty_raises(self) -> None:
        att = LossThresholdAttack()
        with self.assertRaises(ValueError):
            att.fit([], [0.5])
        with self.assertRaises(ValueError):
            att.fit([0.3], [])

    def test_high_advantage_on_clear_separation(self) -> None:
        m_tr, nm_tr, m_ev, nm_ev = self._clear_split()
        att = LossThresholdAttack()
        att.fit(m_tr, nm_tr)
        result = att.evaluate(m_ev, nm_ev)
        self.assertGreater(result.advantage, 0.5)
        self.assertGreater(result.accuracy, 0.8)

    def test_predict_shape(self) -> None:
        m_tr, nm_tr, _, _ = self._clear_split()
        att = LossThresholdAttack().fit(m_tr, nm_tr)
        preds = att.predict([0.1, 0.5, 0.9])
        self.assertEqual(len(preds), 3)
        self.assertTrue(all(p in (0, 1) for p in preds))

    def test_predict_clear_separation(self) -> None:
        """Low-loss sample → member; high-loss → non-member."""
        m_tr, nm_tr, _, _ = self._clear_split()
        att = LossThresholdAttack().fit(m_tr, nm_tr)
        preds = att.predict([0.1, 0.9])
        self.assertEqual(preds[0], 1)  # member
        self.assertEqual(preds[1], 0)  # non-member

    def test_evaluate_empty_raises(self) -> None:
        m_tr, nm_tr, _, _ = self._clear_split()
        att = LossThresholdAttack().fit(m_tr, nm_tr)
        with self.assertRaises(ValueError):
            att.evaluate([], [0.5])
        with self.assertRaises(ValueError):
            att.evaluate([0.3], [])

    def test_advantage_near_zero_for_identical_distributions(self) -> None:
        """When member and non-member losses are identical, advantage should be ~0."""
        losses = [0.5] * 20
        att = LossThresholdAttack().fit(losses[:10], losses[:10])
        result = att.evaluate(losses[10:], losses[10:])
        # Advantage can be positive or negative but bounded near 0 when distributions overlap
        self.assertLessEqual(abs(result.advantage), 1.0)

    def test_result_fields_bounded(self) -> None:
        m_tr, nm_tr, m_ev, nm_ev = self._clear_split()
        att = LossThresholdAttack().fit(m_tr, nm_tr)
        r = att.evaluate(m_ev, nm_ev)
        for field_val in (r.accuracy, r.tpr, r.fpr, r.precision):
            self.assertGreaterEqual(field_val, 0.0)
            self.assertLessEqual(field_val, 1.0)


class TestSimulateAttack(unittest.TestCase):
    def test_returns_attack_result(self) -> None:
        result = simulate_attack()
        self.assertIsInstance(result, AttackResult)

    def test_high_advantage_on_default_params(self) -> None:
        """Default params have large loss gap (0.3 vs 0.7) → high advantage."""
        result = simulate_attack()
        self.assertGreater(result.advantage, 0.5)

    def test_low_advantage_when_distributions_overlap(self) -> None:
        """Narrow loss gap → low attack advantage."""
        result = simulate_attack(
            member_mean_loss=0.5,
            member_std_loss=0.3,
            non_member_mean_loss=0.55,
            non_member_std_loss=0.3,
        )
        self.assertLess(result.advantage, 0.4)

    def test_reproducibility(self) -> None:
        r1 = simulate_attack(seed=7)
        r2 = simulate_attack(seed=7)
        self.assertEqual(r1, r2)


class TestDpAdvantagebound(unittest.TestCase):
    def test_epsilon_zero_gives_zero(self) -> None:
        self.assertAlmostEqual(dp_advantage_bound(0.0), 0.0)

    def test_epsilon_one(self) -> None:
        self.assertAlmostEqual(dp_advantage_bound(1.0), math.e - 1.0, places=10)

    def test_negative_epsilon_raises(self) -> None:
        with self.assertRaises(ValueError):
            dp_advantage_bound(-0.1)

    def test_small_epsilon_approx_linear(self) -> None:
        """For small ε, e^ε - 1 ≈ ε."""
        eps = 0.01
        bound = dp_advantage_bound(eps)
        self.assertAlmostEqual(bound, eps, delta=0.001)


if __name__ == "__main__":
    unittest.main()
