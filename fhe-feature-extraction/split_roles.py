"""Split-role CKKS feature extraction: the data owner keeps the secret key;
the evaluator computes on ciphertext with public evaluation keys only.
"""

import hashlib
from dataclasses import dataclass
from typing import Any

import numpy as np

try:
    import tenseal

    ts: Any = tenseal

    TENSEAL_AVAILABLE = True
except ImportError:
    ts = None
    TENSEAL_AVAILABLE = False


class FHEUnavailableError(RuntimeError):
    """The encrypted computation library is unavailable."""


class KeyBoundaryError(RuntimeError):
    """An evaluator was given secret key material."""


class ContextMismatchError(ValueError):
    """Ciphertext belongs to a different encryption context."""


class IntegrityError(ValueError):
    """A ciphertext does not match its recorded fingerprint."""


@dataclass(frozen=True)
class CKKSParameters:
    """Parameters for the supported CKKS contexts."""

    poly_modulus_degree: int = 8192
    coeff_mod_bit_sizes: tuple[int, ...] = (60, 40, 40, 60)
    global_scale_bits: int = 40

    @property
    def slot_count(self) -> int:
        """Return the CKKS vector slot capacity."""
        return self.poly_modulus_degree // 2

    def validate(self) -> None:
        """Check the supported parameter ranges before creating a context."""
        if self.poly_modulus_degree not in (8192, 16384):
            raise ValueError("poly_modulus_degree must be 8192 or 16384")
        if len(self.coeff_mod_bit_sizes) < 3:
            raise ValueError("coeff_mod_bit_sizes needs at least three primes")
        if not 20 <= self.global_scale_bits <= 60:
            raise ValueError("global_scale_bits must be between 20 and 60")


def validate_vector(vector: Any, max_length: int) -> np.ndarray:
    """Convert a finite, nonempty vector within the slot capacity to float64."""
    values = np.asarray(vector, dtype=np.float64)
    if values.ndim != 1:
        raise ValueError("input must be one-dimensional")
    if values.size == 0:
        raise ValueError("input must not be empty")
    if values.size > max_length:
        raise ValueError(f"input length {values.size} exceeds slot capacity {max_length}")
    if not np.all(np.isfinite(values)):
        raise ValueError("input contains NaN or infinity")
    return values


def validate_projection(projection: Any) -> np.ndarray:
    """Convert a finite, nonempty projection matrix to float64."""
    matrix = np.asarray(projection, dtype=np.float64)
    if matrix.ndim != 2:
        raise ValueError("projection must be two-dimensional")
    if 0 in matrix.shape:
        raise ValueError("projection must not be empty")
    if not np.all(np.isfinite(matrix)):
        raise ValueError("projection contains NaN or infinity")
    return matrix


def fingerprint(data: bytes) -> str:
    """Return a SHA-256 fingerprint for accidental-corruption detection."""
    return hashlib.sha256(data).hexdigest()


def _require_tenseal() -> None:
    if not TENSEAL_AVAILABLE:
        raise FHEUnavailableError("TenSEAL is required: pip install -e .[fhe]")


@dataclass(frozen=True)
class EncryptedInput:
    """Serialized encrypted input with its dimension and context identifier."""

    ciphertext: bytes
    input_dim: int
    context_id: str


@dataclass(frozen=True)
class EncryptedFeatures:
    """Serialized encrypted scalars and their unkeyed fingerprints."""

    ciphertexts: tuple[bytes, ...]
    fingerprints: tuple[str, ...]
    context_id: str


class DataOwner:
    """Holds the secret key, encrypts inputs, and decrypts only the derived features."""

    def __init__(self, params: CKKSParameters | None = None) -> None:
        """Create a private context and serialize only public evaluation keys."""
        _require_tenseal()
        self.params = params or CKKSParameters()
        self.params.validate()
        self._context = ts.context(
            ts.SCHEME_TYPE.CKKS,
            poly_modulus_degree=self.params.poly_modulus_degree,
            coeff_mod_bit_sizes=list(self.params.coeff_mod_bit_sizes),
        )
        self._context.global_scale = 2**self.params.global_scale_bits
        self._context.generate_galois_keys()
        self._public_context = self._context.serialize(
            save_public_key=True,
            save_secret_key=False,
            save_galois_keys=True,
            save_relin_keys=True,
        )
        self.context_id = fingerprint(self._public_context)

    def public_context(self) -> bytes:
        """Return serialized public evaluation keys without the secret key."""
        return self._public_context

    def encrypt(self, vector: Any) -> EncryptedInput:
        """Encrypt a validated input under the owner's context."""
        values = validate_vector(vector, self.params.slot_count)
        encrypted = ts.ckks_vector(self._context, values.tolist())
        return EncryptedInput(encrypted.serialize(), int(values.size), self.context_id)

    def decrypt_features(self, features: EncryptedFeatures, expected_count: int) -> np.ndarray:
        """Check context, count, and fingerprints before decrypting derived scalars."""
        if features.context_id != self.context_id:
            raise ContextMismatchError("features were produced under a different context")
        if (
            len(features.ciphertexts) != expected_count
            or len(features.fingerprints) != expected_count
        ):
            raise ValueError("feature count mismatch")
        for i, data in enumerate(features.ciphertexts):
            if fingerprint(data) != features.fingerprints[i]:
                raise IntegrityError(f"ciphertext {i} failed its integrity check")
        return np.asarray(
            [
                ts.ckks_vector_from(self._context, data).decrypt()[0]
                for data in features.ciphertexts
            ],
            dtype=np.float64,
        )


class Evaluator:
    """Computes encrypted dot products with public evaluation keys; it never holds a secret key."""

    def __init__(self, public_context: bytes, projection: Any, global_scale_bits: int = 40) -> None:
        """Load a public context and reject any context containing a secret key."""
        _require_tenseal()
        context = ts.context_from(public_context)
        if context.is_private():
            raise KeyBoundaryError("evaluator context must not contain a secret key")
        context.global_scale = 2**global_scale_bits
        self._context = context
        self.context_id = fingerprint(public_context)
        self.projection = validate_projection(projection)

    def evaluate(self, encrypted: EncryptedInput) -> EncryptedFeatures:
        """Compute one encrypted dot product for each public projection row."""
        if encrypted.context_id != self.context_id:
            raise ContextMismatchError("ciphertext was produced under a different context")
        if self.projection.shape[1] != encrypted.input_dim:
            raise ValueError("projection width does not match input length")
        vector = ts.ckks_vector_from(self._context, encrypted.ciphertext)
        outputs = []
        for row in self.projection:
            result = vector.dot(row.tolist())
            outputs.append(result.serialize())
        return EncryptedFeatures(
            tuple(outputs), tuple(fingerprint(data) for data in outputs), self.context_id
        )


def plaintext_features(vector: Any, projection: Any) -> np.ndarray:
    """Compute the plaintext reference for a validated vector and projection."""
    matrix = validate_projection(projection)
    values = validate_vector(vector, matrix.shape[1])
    if values.size != matrix.shape[1]:
        raise ValueError("projection width does not match input length")
    return matrix @ values


def run_split_roles_demo(
    input_dim: int = 128, feature_dim: int = 16, seed: int = 7
) -> dict[str, Any]:
    """Compare split-role encrypted features with a seeded synthetic reference."""
    rng = np.random.default_rng(seed)
    vector = rng.standard_normal(input_dim)
    projection = rng.standard_normal((feature_dim, input_dim))
    projection /= np.linalg.norm(projection, axis=1, keepdims=True)
    owner = DataOwner()
    evaluator = Evaluator(owner.public_context(), projection)
    encrypted = owner.encrypt(vector)
    features = evaluator.evaluate(encrypted)
    output = owner.decrypt_features(features, expected_count=feature_dim)
    return {
        "input_dim": input_dim,
        "feature_dim": feature_dim,
        "seed": seed,
        "max_abs_error": float(np.max(np.abs(output - plaintext_features(vector, projection)))),
        "input_ciphertext_bytes": len(encrypted.ciphertext),
        "feature_ciphertext_bytes": sum(len(data) for data in features.ciphertexts),
        "mode": "split-roles-tenseal",
    }
