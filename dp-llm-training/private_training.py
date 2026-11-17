"""Differentially private training with Opacus: per-sample clipping,
Gaussian noise, and a pre-step privacy-budget guard.
"""

import importlib.util
import math
from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np

TORCH_AVAILABLE = importlib.util.find_spec("torch") is not None
OPACUS_AVAILABLE = importlib.util.find_spec("opacus") is not None


class PrivateTrainingUnavailableError(RuntimeError):
    """The libraries needed for private training are unavailable."""


@dataclass(frozen=True)
class PrivateTrainingConfig:
    """Training parameters and the maximum allowed privacy expenditure."""

    target_epsilon: float = 3.0
    target_delta: float = 1e-5
    noise_multiplier: float = 1.2
    max_grad_norm: float = 1.0
    batch_size: int = 64
    epochs: int = 3
    learning_rate: float = 0.1
    seed: int = 0

    def validate(self, dataset_size: int) -> None:
        """Check privacy and optimizer settings against the dataset size."""
        if any(
            not math.isfinite(value) or value <= 0
            for value in (
                self.target_epsilon,
                self.noise_multiplier,
                self.max_grad_norm,
                self.learning_rate,
            )
        ):
            raise ValueError(
                "target_epsilon, noise_multiplier, max_grad_norm, and learning_rate must be finite and positive"
            )
        if dataset_size <= 0 or not 0 < self.target_delta < 1 / dataset_size:
            raise ValueError("target_delta must be smaller than 1 / dataset_size")
        if not 0 < self.batch_size < dataset_size:
            raise ValueError("batch_size must be positive and smaller than dataset_size")
        if self.epochs < 1:
            raise ValueError("epochs must be at least 1")


def make_synthetic_classification(
    n_records: int = 2048, n_features: int = 8, seed: int = 0
) -> tuple[np.ndarray, np.ndarray]:
    """Generate seeded synthetic features with binary linear labels."""
    rng = np.random.default_rng(seed)
    features = rng.standard_normal((n_records, n_features)).astype(np.float32)
    weights = rng.standard_normal(n_features)
    labels = (features @ weights > 0).astype(np.int64)
    return features, labels


def build_reference_model(n_features: int = 8, hidden: int = 16) -> Any:
    """Build the small reference classifier with per-sample-compatible layers."""
    import torch

    return torch.nn.Sequential(
        torch.nn.Linear(n_features, hidden), torch.nn.ReLU(), torch.nn.Linear(hidden, 2)
    )


@dataclass
class EpochRecord:
    """Privacy expenditure and mean training loss at an epoch boundary."""

    epoch: int
    cumulative_steps: int
    epsilon_spent: float
    delta: float
    loss: float
    budget_fraction: float
    budget_exhausted: bool


@dataclass
class PrivateTrainingReport:
    """Summary of an Opacus run and its completed or partially completed epochs."""

    config: PrivateTrainingConfig
    dataset_size: int
    sample_rate: float
    steps: int
    stopped_reason: str
    final_epsilon: float
    records: list[EpochRecord] = field(default_factory=list)

    def to_audit_log(self, provenance: dict[str, Any] | None = None) -> dict[str, Any]:
        """Export records and the private-training accounting metadata."""
        if not self.records:
            raise ValueError("no completed training epochs to record")
        return {
            "metadata": {
                "target_epsilon": self.config.target_epsilon,
                "target_delta": self.config.target_delta,
                "noise_multiplier": self.config.noise_multiplier,
                "max_grad_norm": self.config.max_grad_norm,
                "sample_rate": self.sample_rate,
                "training_mode": "private",
                "accounting_source": "opacus-rdp",
                "dataset": {
                    "name": "synthetic-linear-binary",
                    "n_records": self.dataset_size,
                    "seed": self.config.seed,
                },
                "provenance": provenance,
            },
            "log": [asdict(record) for record in self.records],
        }


class PrivateTrainer:
    """Train with an attached Opacus accountant and a pre-step budget guard."""

    def __init__(
        self,
        model: Any,
        features: np.ndarray,
        labels: np.ndarray,
        config: PrivateTrainingConfig | None = None,
    ) -> None:
        """Wrap a compatible model, optimizer, and loader with Opacus."""
        if not TORCH_AVAILABLE or not OPACUS_AVAILABLE:
            raise PrivateTrainingUnavailableError(
                "private training requires torch and opacus: pip install -e .[dp]"
            )
        import torch
        from opacus import PrivacyEngine
        from opacus.optimizers import DPOptimizer
        from opacus.validators import ModuleValidator
        from torch.utils.data import DataLoader, TensorDataset

        self.config = config or PrivateTrainingConfig()
        self.config.validate(len(features))
        problems = ModuleValidator.validate(model, strict=False)
        if problems:
            raise ValueError(f"model is not compatible with per-sample gradients: {problems}")
        torch.manual_seed(self.config.seed)
        dataset = TensorDataset(
            torch.as_tensor(features, dtype=torch.float32),
            torch.as_tensor(labels, dtype=torch.long),
        )
        loader = DataLoader(dataset, batch_size=self.config.batch_size, shuffle=False)
        self.sample_rate = 1.0 / len(loader)
        optimizer = torch.optim.SGD(model.parameters(), lr=self.config.learning_rate)
        self.engine = PrivacyEngine(accountant="rdp")
        self.model, self.optimizer, self.loader = self.engine.make_private(
            module=model,
            optimizer=optimizer,
            data_loader=loader,
            noise_multiplier=self.config.noise_multiplier,
            max_grad_norm=self.config.max_grad_norm,
        )
        if not isinstance(self.optimizer, DPOptimizer):
            raise RuntimeError("Opacus did not return a DPOptimizer")
        self.criterion = torch.nn.CrossEntropyLoss()
        self.dataset_size = len(features)
        self.steps = 0

    def spent_epsilon(self) -> float:
        """Read privacy expenditure from the accountant attached to this run."""
        if self.steps == 0:
            return 0.0
        return float(self.engine.get_epsilon(self.config.target_delta))

    def predicted_epsilon_after_next_step(self) -> float:
        """Probe the next step on a copied accountant without changing the run."""
        from opacus.accountants import RDPAccountant

        probe = RDPAccountant()
        probe.history = list(self.engine.accountant.history)
        probe.step(noise_multiplier=self.config.noise_multiplier, sample_rate=self.sample_rate)
        return float(probe.get_epsilon(delta=self.config.target_delta))

    def train(self) -> PrivateTrainingReport:
        """Apply only steps whose predicted privacy expenditure fits the target."""
        records = []
        stopped_reason = "completed"
        self.model.train()
        for epoch in range(1, self.config.epochs + 1):
            losses = []
            for features, labels in self.loader:
                if self.predicted_epsilon_after_next_step() > self.config.target_epsilon:
                    stopped_reason = "budget"
                    break
                self.optimizer.zero_grad()
                loss = self.criterion(self.model(features), labels)
                loss.backward()
                self.optimizer.step()
                self.steps += 1
                if features.shape[0] > 0:
                    losses.append(float(loss.item()))
            if losses:
                epsilon = round(self.spent_epsilon(), 6)
                records.append(
                    EpochRecord(
                        epoch,
                        self.steps,
                        epsilon,
                        self.config.target_delta,
                        round(sum(losses) / len(losses), 6),
                        round(min(epsilon / self.config.target_epsilon, 1.0), 6),
                        epsilon >= self.config.target_epsilon,
                    )
                )
            if stopped_reason == "budget":
                break
        return PrivateTrainingReport(
            config=self.config,
            dataset_size=self.dataset_size,
            sample_rate=self.sample_rate,
            steps=self.steps,
            stopped_reason=stopped_reason,
            final_epsilon=round(self.spent_epsilon(), 6),
            records=records,
        )


def run_private_demo(seed: int = 0) -> PrivateTrainingReport:
    """Run private training on the seeded synthetic reference dataset."""
    import torch

    features, labels = make_synthetic_classification(seed=seed)
    torch.manual_seed(seed)
    model = build_reference_model()
    return PrivateTrainer(model, features, labels, PrivateTrainingConfig(seed=seed)).train()
