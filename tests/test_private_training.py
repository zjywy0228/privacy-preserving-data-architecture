"""Verify private optimizer wiring, accounting, and the pre-step budget guard."""

import json
import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "dp-llm-training"))
import private_training  # noqa: E402
from private_training import (  # noqa: E402
    PrivateTrainer,
    PrivateTrainingConfig,
    PrivateTrainingReport,
    PrivateTrainingUnavailableError,
    build_reference_model,
    make_synthetic_classification,
)
from validate_audit_log import validate_log  # noqa: E402


def test_config_rejects_delta_not_below_inverse_size():
    with pytest.raises(ValueError, match="target_delta"):
        PrivateTrainingConfig(target_delta=0.02).validate(100)


@pytest.mark.parametrize(
    "overrides",
    [
        {"noise_multiplier": 0},
        {"max_grad_norm": 0},
        {"learning_rate": 0},
        {"epochs": 0},
        {"target_epsilon": float("nan")},
        {"noise_multiplier": float("inf")},
    ],
)
def test_config_rejects_nonpositive_values(overrides):
    with pytest.raises(ValueError):
        PrivateTrainingConfig(**overrides).validate(1000)


def test_config_rejects_batch_not_smaller_than_dataset():
    with pytest.raises(ValueError, match="batch_size"):
        PrivateTrainingConfig(batch_size=100).validate(100)


def test_synthetic_classification_is_deterministic_and_balanced():
    features, labels = make_synthetic_classification(seed=0)
    repeated_features, repeated_labels = make_synthetic_classification(seed=0)
    np.testing.assert_array_equal(features, repeated_features)
    np.testing.assert_array_equal(labels, repeated_labels)
    assert set(labels) == {0, 1}


def test_trainer_requires_torch_and_opacus(monkeypatch):
    features, labels = make_synthetic_classification(512, 8, 0)
    monkeypatch.setattr(private_training, "OPACUS_AVAILABLE", False)
    with pytest.raises(PrivateTrainingUnavailableError, match="requires torch and opacus"):
        PrivateTrainer(None, features, labels)


def test_audit_log_requires_records():
    report = PrivateTrainingReport(PrivateTrainingConfig(), 512, 0.125, 0, "budget", 0.0)
    with pytest.raises(ValueError, match="no completed training epochs"):
        report.to_audit_log()


def test_make_private_returns_dp_optimizer():
    pytest.importorskip("torch")
    pytest.importorskip("opacus")
    from opacus.optimizers import DPOptimizer

    features, labels = make_synthetic_classification(512, 8, 0)
    trainer = PrivateTrainer(build_reference_model(), features, labels)
    assert isinstance(trainer.optimizer, DPOptimizer)
    assert trainer.optimizer.noise_multiplier == trainer.config.noise_multiplier
    assert trainer.optimizer.max_grad_norm == trainer.config.max_grad_norm


def test_backward_produces_per_sample_gradients():
    pytest.importorskip("torch")
    pytest.importorskip("opacus")
    features, labels = make_synthetic_classification(512, 8, 0)
    trainer = PrivateTrainer(build_reference_model(), features, labels)
    batch, targets = next(iter(trainer.loader))
    trainer.criterion(trainer.model(batch), targets).backward()
    for parameter in trainer.model.parameters():
        if parameter.requires_grad:
            assert parameter.grad_sample.shape[0] == len(batch)


def test_training_completes_with_large_budget():
    pytest.importorskip("torch")
    pytest.importorskip("opacus")
    features, labels = make_synthetic_classification(512, 8, 0)
    trainer = PrivateTrainer(
        build_reference_model(),
        features,
        labels,
        PrivateTrainingConfig(target_epsilon=50, batch_size=64, epochs=2),
    )
    report = trainer.train()
    assert report.stopped_reason == "completed"
    assert report.steps == 2 * len(trainer.loader)
    assert len(report.records) == 2
    assert report.records[1].epsilon_spent > report.records[0].epsilon_spent
    assert report.final_epsilon == round(trainer.engine.get_epsilon(trainer.config.target_delta), 6)
    assert sum(item[2] for item in trainer.engine.accountant.history) == report.steps


@pytest.mark.parametrize("target", [0.5, 2.0])
def test_budget_guard_never_exceeds_target(target):
    pytest.importorskip("torch")
    pytest.importorskip("opacus")
    features, labels = make_synthetic_classification(512, 8, 0)
    trainer = PrivateTrainer(
        build_reference_model(),
        features,
        labels,
        PrivateTrainingConfig(target_epsilon=target),
    )
    report = trainer.train()
    assert report.stopped_reason == "budget"
    assert report.final_epsilon <= target
    assert trainer.spent_epsilon() <= target
    assert trainer.predicted_epsilon_after_next_step() > target
    assert sum(item[2] for item in trainer.engine.accountant.history) == report.steps
    if target == 0.5:
        assert report.steps == 0
    else:
        assert report.steps > 0


def test_audit_log_passes_validator(tmp_path):
    pytest.importorskip("torch")
    pytest.importorskip("opacus")
    features, labels = make_synthetic_classification(512, 8, 0)
    trainer = PrivateTrainer(
        build_reference_model(),
        features,
        labels,
        PrivateTrainingConfig(target_epsilon=50, batch_size=64, epochs=2),
    )
    path = tmp_path / "audit.json"
    payload = trainer.train().to_audit_log()
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert payload["metadata"]["training_mode"] == "private"
    assert payload["metadata"]["accounting_source"] == "opacus-rdp"
    assert validate_log(path).passed is True
