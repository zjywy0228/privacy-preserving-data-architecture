"""Coordinate federated aggregation of serialized FHE ciphertext updates.

The coordinator never converts an update to a NumPy array or plaintext. A
backend receives opaque ciphertext bytes and returns an aggregated ciphertext.
`TenSEALCKKSBackend` is the production-oriented adapter; `MockVectorBackend` is
explicitly non-cryptographic and exists only for tests and CI.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Protocol

FLOWER_TENSOR_TYPE = "fhe.ckks.serialized.v1"


class CiphertextAggregationBackend(Protocol):
    """Backend contract for encrypted mean aggregation."""

    def aggregate_mean(self, payloads: list[bytes]) -> bytes:
        """Return an encrypted mean without exposing plaintext to the caller."""


@dataclass(frozen=True)
class EncryptedUpdate:
    """One client update transported as opaque serialized ciphertext."""

    client_id: str
    round_id: int
    payload: bytes


@dataclass(frozen=True)
class AuditEntry:
    """Data-minimized receipt record; ciphertext content is not retained here."""

    event: str
    round_id: int
    client_id: str | None
    payload_sha256: str
    payload_bytes: int
    timestamp_utc: str


class FederatedFHECoordinator:
    """Authorize, audit, and aggregate encrypted client updates by round."""

    def __init__(
        self,
        authorized_clients: set[str],
        backend: CiphertextAggregationBackend,
        min_clients: int = 2,
        max_update_bytes: int = 16 * 1024 * 1024,
    ) -> None:
        if not authorized_clients or any(not client for client in authorized_clients):
            raise ValueError("authorized_clients must contain non-empty client IDs.")
        if min_clients < 2 or min_clients > len(authorized_clients):
            raise ValueError("min_clients must be between 2 and the client count.")
        if max_update_bytes <= 0:
            raise ValueError("max_update_bytes must be positive.")

        self.authorized_clients = frozenset(authorized_clients)
        self.backend = backend
        self.min_clients = min_clients
        self.max_update_bytes = max_update_bytes
        self._round_id: int | None = None
        self._updates: dict[str, bytes] = {}
        self._audit: list[AuditEntry] = []

    @property
    def active_round(self) -> int | None:
        return self._round_id

    @property
    def ready(self) -> bool:
        return self._round_id is not None and len(self._updates) >= self.min_clients

    def start_round(self, round_id: int) -> None:
        if round_id < 0:
            raise ValueError("round_id must be non-negative.")
        if self._round_id is not None:
            raise RuntimeError("The active round must be aggregated before starting another.")
        self._round_id = round_id
        self._updates = {}

    def submit(self, update: EncryptedUpdate) -> None:
        if self._round_id is None:
            raise RuntimeError("No federated round is active.")
        if update.round_id != self._round_id:
            raise ValueError(
                f"Update round {update.round_id} does not match active round {self._round_id}."
            )
        if update.client_id not in self.authorized_clients:
            raise PermissionError(f"Client {update.client_id!r} is not authorized.")
        if update.client_id in self._updates:
            raise ValueError(f"Client {update.client_id!r} already submitted this round.")
        if not isinstance(update.payload, bytes) or not update.payload:
            raise ValueError("Encrypted payload must be non-empty bytes.")
        if len(update.payload) > self.max_update_bytes:
            raise ValueError("Encrypted payload exceeds max_update_bytes.")

        self._updates[update.client_id] = update.payload
        self._audit.append(
            AuditEntry(
                event="client_update_received",
                round_id=update.round_id,
                client_id=update.client_id,
                payload_sha256=hashlib.sha256(update.payload).hexdigest(),
                payload_bytes=len(update.payload),
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
            )
        )

    def aggregate_mean(self) -> bytes:
        if self._round_id is None:
            raise RuntimeError("No federated round is active.")
        if not self.ready:
            raise RuntimeError(
                f"Round requires {self.min_clients} clients; received {len(self._updates)}."
            )

        round_id = self._round_id
        aggregate = self.backend.aggregate_mean(list(self._updates.values()))
        if not isinstance(aggregate, bytes) or not aggregate:
            raise ValueError("Aggregation backend returned no serialized ciphertext.")
        self._audit.append(
            AuditEntry(
                event="encrypted_mean_created",
                round_id=round_id,
                client_id=None,
                payload_sha256=hashlib.sha256(aggregate).hexdigest(),
                payload_bytes=len(aggregate),
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
            )
        )
        self._round_id = None
        self._updates = {}
        return aggregate

    def audit_log(self) -> list[dict[str, Any]]:
        """Return receipt metadata without ciphertext payloads."""
        return [asdict(entry) for entry in self._audit]


class MockVectorBackend:
    """Non-cryptographic vector codec and backend for tests only."""

    MAGIC = b"MOCK-NOT-ENCRYPTED:"

    @classmethod
    def encode(cls, values: list[float]) -> bytes:
        if not values or any(not math.isfinite(value) for value in values):
            raise ValueError("Mock vectors must contain finite values.")
        return cls.MAGIC + json.dumps(values, separators=(",", ":")).encode("utf-8")

    @classmethod
    def decode(cls, payload: bytes) -> list[float]:
        if not payload.startswith(cls.MAGIC):
            raise ValueError("Payload is not a mock vector.")
        values = json.loads(payload[len(cls.MAGIC) :].decode("utf-8"))
        if not isinstance(values, list) or not values:
            raise ValueError("Mock payload must contain a non-empty vector.")
        parsed = [float(value) for value in values]
        if any(not math.isfinite(value) for value in parsed):
            raise ValueError("Mock vectors must contain finite values.")
        return parsed

    def aggregate_mean(self, payloads: list[bytes]) -> bytes:
        if not payloads:
            raise ValueError("At least one payload is required.")
        vectors = [self.decode(payload) for payload in payloads]
        width = len(vectors[0])
        if any(len(vector) != width for vector in vectors):
            raise ValueError("All encrypted update vectors must have the same width.")
        mean = [sum(vector[index] for vector in vectors) / len(vectors) for index in range(width)]
        return self.encode(mean)


class TenSEALCKKSBackend:
    """Aggregate serialized TenSEAL CKKS vectors without a secret key."""

    def __init__(self, public_context: Any) -> None:
        try:
            import tenseal as ts
        except ImportError as exc:
            raise RuntimeError(
                "TenSEAL is required for TenSEALCKKSBackend; install the federated extra."
            ) from exc
        self._ts = ts
        self._context = public_context

    def aggregate_mean(self, payloads: list[bytes]) -> bytes:
        if not payloads:
            raise ValueError("At least one ciphertext payload is required.")
        vectors = [self._ts.ckks_vector_from(self._context, payload) for payload in payloads]
        total = vectors[0]
        for vector in vectors[1:]:
            total += vector
        total *= 1.0 / len(vectors)
        return bytes(total.serialize())


def to_flower_parameters(payload: bytes) -> Any:
    """Wrap one serialized ciphertext for Flower transport."""
    if not isinstance(payload, bytes) or not payload:
        raise ValueError("Encrypted payload must be non-empty bytes.")
    try:
        from flwr.common import Parameters
    except ImportError as exc:
        raise RuntimeError(
            "Flower is required for transport helpers; install the federated extra."
        ) from exc
    return Parameters(tensors=[payload], tensor_type=FLOWER_TENSOR_TYPE)


def from_flower_parameters(parameters: Any) -> bytes:
    """Extract one serialized ciphertext without NumPy/plaintext conversion."""
    if getattr(parameters, "tensor_type", None) != FLOWER_TENSOR_TYPE:
        raise ValueError(f"Expected Flower tensor_type {FLOWER_TENSOR_TYPE!r}.")
    tensors = getattr(parameters, "tensors", None)
    if not isinstance(tensors, list) or len(tensors) != 1:
        raise ValueError("Flower parameters must contain exactly one ciphertext tensor.")
    payload = tensors[0]
    if not isinstance(payload, bytes) or not payload:
        raise ValueError("Flower ciphertext tensor must be non-empty bytes.")
    return payload
