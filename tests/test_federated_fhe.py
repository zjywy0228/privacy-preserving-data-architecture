"""Mock-safe tests for federated transport of serialized FHE updates."""

from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "fhe-feature-extraction"))

from federated import (  # noqa: E402
    FLOWER_TENSOR_TYPE,
    EncryptedUpdate,
    FederatedFHECoordinator,
    MockVectorBackend,
    from_flower_parameters,
)


def _coordinator(**overrides) -> FederatedFHECoordinator:
    values = {
        "authorized_clients": {"hospital-a", "university-b", "lab-c"},
        "backend": MockVectorBackend(),
        "min_clients": 2,
        "max_update_bytes": 4096,
    }
    values.update(overrides)
    return FederatedFHECoordinator(**values)


def _update(client_id: str, values: list[float], round_id: int = 1) -> EncryptedUpdate:
    return EncryptedUpdate(
        client_id=client_id,
        round_id=round_id,
        payload=MockVectorBackend.encode(values),
    )


def test_mock_backend_aggregates_vector_mean() -> None:
    backend = MockVectorBackend()
    result = backend.aggregate_mean([backend.encode([1.0, 3.0]), backend.encode([3.0, 5.0])])

    assert backend.decode(result) == [2.0, 4.0]
    assert result.startswith(b"MOCK-NOT-ENCRYPTED:")


def test_coordinator_aggregates_authorized_clients_and_closes_round() -> None:
    coordinator = _coordinator()
    coordinator.start_round(1)
    coordinator.submit(_update("hospital-a", [1.0, 2.0]))
    coordinator.submit(_update("university-b", [3.0, 4.0]))

    assert coordinator.ready
    aggregate = coordinator.aggregate_mean()

    assert MockVectorBackend.decode(aggregate) == [2.0, 3.0]
    assert coordinator.active_round is None
    assert not coordinator.ready


def test_audit_log_contains_hashes_but_not_payloads() -> None:
    coordinator = _coordinator()
    update = _update("hospital-a", [1.0, 2.0])
    coordinator.start_round(1)
    coordinator.submit(update)
    coordinator.submit(_update("university-b", [3.0, 4.0]))
    coordinator.aggregate_mean()

    audit = coordinator.audit_log()
    assert audit[0]["payload_sha256"] == hashlib.sha256(update.payload).hexdigest()
    assert audit[0]["client_id"] == "hospital-a"
    assert audit[-1]["event"] == "encrypted_mean_created"
    assert all("payload" not in entry for entry in audit)


def test_unauthorized_client_is_rejected() -> None:
    coordinator = _coordinator()
    coordinator.start_round(1)

    with pytest.raises(PermissionError):
        coordinator.submit(_update("unknown-client", [1.0]))


def test_wrong_round_and_duplicate_submission_are_rejected() -> None:
    coordinator = _coordinator()
    coordinator.start_round(1)

    with pytest.raises(ValueError, match="does not match"):
        coordinator.submit(_update("hospital-a", [1.0], round_id=2))

    coordinator.submit(_update("hospital-a", [1.0]))
    with pytest.raises(ValueError, match="already submitted"):
        coordinator.submit(_update("hospital-a", [2.0]))


def test_threshold_is_enforced_before_aggregation() -> None:
    coordinator = _coordinator()
    coordinator.start_round(1)
    coordinator.submit(_update("hospital-a", [1.0]))

    with pytest.raises(RuntimeError, match="requires 2 clients"):
        coordinator.aggregate_mean()


def test_payload_size_and_empty_payload_are_rejected() -> None:
    coordinator = _coordinator(max_update_bytes=4)
    coordinator.start_round(1)

    with pytest.raises(ValueError, match="non-empty bytes"):
        coordinator.submit(EncryptedUpdate("hospital-a", 1, b""))
    with pytest.raises(ValueError, match="exceeds"):
        coordinator.submit(EncryptedUpdate("hospital-a", 1, b"12345"))


def test_mismatched_vector_widths_are_rejected() -> None:
    backend = MockVectorBackend()

    with pytest.raises(ValueError, match="same width"):
        backend.aggregate_mean([backend.encode([1.0]), backend.encode([1.0, 2.0])])


def test_new_round_cannot_start_while_round_is_active() -> None:
    coordinator = _coordinator()
    coordinator.start_round(1)

    with pytest.raises(RuntimeError, match="active round"):
        coordinator.start_round(2)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"authorized_clients": set()},
        {"authorized_clients": {""}},
        {"min_clients": 1},
        {"min_clients": 4},
        {"max_update_bytes": 0},
    ],
)
def test_invalid_coordinator_configuration_is_rejected(kwargs: dict) -> None:
    with pytest.raises(ValueError):
        _coordinator(**kwargs)


@dataclass
class DummyParameters:
    tensors: list[bytes]
    tensor_type: str


def test_flower_parameters_are_unwrapped_without_conversion() -> None:
    payload = b"serialized-ciphertext"
    parameters = DummyParameters([payload], FLOWER_TENSOR_TYPE)

    assert from_flower_parameters(parameters) is payload


@pytest.mark.parametrize(
    "parameters",
    [
        DummyParameters([b"cipher"], "numpy.ndarray"),
        DummyParameters([], FLOWER_TENSOR_TYPE),
        DummyParameters([b"a", b"b"], FLOWER_TENSOR_TYPE),
        DummyParameters([b""], FLOWER_TENSOR_TYPE),
    ],
)
def test_invalid_flower_parameters_are_rejected(parameters: DummyParameters) -> None:
    with pytest.raises(ValueError):
        from_flower_parameters(parameters)
