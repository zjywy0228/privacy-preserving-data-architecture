"""
Tests for budget_accountant.BudgetAccountant

These tests require no Opacus or PyTorch installation.  All epsilon
computations use the self-contained RDP approximation inside budget_accountant.
"""

import json
import os
import sys
import tempfile
import unittest

# ---------------------------------------------------------------------------
# Path setup so tests can be run from the repo root without installing the pkg
# ---------------------------------------------------------------------------
_DP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dp-llm-training"))
if _DP_DIR not in sys.path:
    sys.path.insert(0, _DP_DIR)

from budget_accountant import BudgetAccountant  # noqa: E402


# ---------------------------------------------------------------------------
# Shared fixture parameters
# ---------------------------------------------------------------------------
TARGET_EPSILON = 3.0
TARGET_DELTA = 1e-5
NOISE_MULTIPLIER = 1.1
SAMPLE_RATE = 64 / 5000   # batch_size=64, dataset_size=5000
STEPS_PER_EPOCH = 5000 // 64  # 78


def _make_accountant(**overrides) -> BudgetAccountant:
    """Return a BudgetAccountant with default test parameters."""
    kwargs = dict(
        target_epsilon=TARGET_EPSILON,
        target_delta=TARGET_DELTA,
        noise_multiplier=NOISE_MULTIPLIER,
        sample_rate=SAMPLE_RATE,
    )
    kwargs.update(overrides)
    return BudgetAccountant(**kwargs)


class TestBudgetAccountantInitial(unittest.TestCase):

    def test_initial_budget_is_full(self):
        """remaining_budget() equals target_epsilon before any epochs are recorded."""
        acc = _make_accountant()
        self.assertAlmostEqual(acc.remaining_budget(), TARGET_EPSILON, places=10)


class TestEpsilonGrowth(unittest.TestCase):

    def test_epsilon_grows_monotonically(self):
        """Epsilon spent must strictly increase with each recorded epoch."""
        acc = _make_accountant()
        epsilons = []
        for epoch in range(1, 4):
            entry = acc.record_epoch(epoch=epoch, steps_in_epoch=STEPS_PER_EPOCH, loss=1.0)
            epsilons.append(entry["epsilon_spent"])

        self.assertEqual(len(epsilons), 3)
        self.assertLess(epsilons[0], epsilons[1])
        self.assertLess(epsilons[1], epsilons[2])


class TestBudgetFraction(unittest.TestCase):

    def test_budget_fraction_bounded_zero_to_one(self):
        """budget_fraction in every log entry must be in [0.0, 1.0]."""
        acc = _make_accountant()
        for epoch in range(1, 6):
            entry = acc.record_epoch(epoch=epoch, steps_in_epoch=STEPS_PER_EPOCH, loss=0.5)
            self.assertGreaterEqual(entry["budget_fraction"], 0.0,
                                    f"budget_fraction < 0 at epoch {epoch}")
            self.assertLessEqual(entry["budget_fraction"], 1.0,
                                 f"budget_fraction > 1 at epoch {epoch}")


class TestSaveLoadRoundtrip(unittest.TestCase):

    def test_save_and_load_roundtrip(self):
        """save_log followed by load_log returns the same number of records."""
        acc = _make_accountant()
        for epoch in range(1, 4):
            acc.record_epoch(epoch=epoch, steps_in_epoch=STEPS_PER_EPOCH, loss=float(epoch))

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json",
                                         delete=False) as tmp:
            tmp_path = tmp.name

        try:
            acc.save_log(tmp_path)
            loaded = BudgetAccountant.load_log(tmp_path)
            self.assertEqual(len(loaded), 3)

            # Verify the file is valid JSON with expected structure
            with open(tmp_path, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
            self.assertIn("metadata", raw)
            self.assertIn("log", raw)
        finally:
            os.unlink(tmp_path)


class TestRecordReturnShape(unittest.TestCase):

    def test_record_returns_dict_with_expected_keys(self):
        """record_epoch() return value must contain all required keys."""
        acc = _make_accountant()
        entry = acc.record_epoch(epoch=1, steps_in_epoch=STEPS_PER_EPOCH, loss=2.0)

        required_keys = {"epoch", "epsilon_spent", "budget_fraction", "budget_exhausted",
                         "cumulative_steps", "delta", "loss"}
        for key in required_keys:
            self.assertIn(key, entry, f"Missing key '{key}' in record_epoch() result")


class TestBudgetExhaustedFlag(unittest.TestCase):

    def test_budget_exhausted_flag(self):
        """With a tiny target_epsilon, budget_exhausted must become True after few steps."""
        # target_epsilon=0.01 is extremely tight; even 1 epoch of 78 steps
        # at typical noise will blow through it.
        acc = _make_accountant(target_epsilon=0.01)
        entry = acc.record_epoch(epoch=1, steps_in_epoch=STEPS_PER_EPOCH, loss=1.0)

        self.assertTrue(
            entry["budget_exhausted"],
            "budget_exhausted should be True when epsilon_spent >= target_epsilon"
        )
        self.assertGreaterEqual(entry["epsilon_spent"], 0.01)
        self.assertEqual(acc.remaining_budget(), 0.0)


if __name__ == "__main__":
    unittest.main()
