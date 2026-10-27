"""Verify the split-role key boundary and encrypted feature extraction."""

import inspect
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "fhe-feature-extraction"))
import split_roles  # noqa: E402
from split_roles import (  # noqa: E402
    CKKSParameters,
    ContextMismatchError,
    DataOwner,
    Evaluator,
    FHEUnavailableError,
    IntegrityError,
    KeyBoundaryError,
    validate_projection,
    validate_vector,
)


@pytest.fixture(scope="module")
def owner_and_projection():
    pytest.importorskip("tenseal")
    owner = DataOwner()
    projection = np.random.default_rng(0).standard_normal((8, 64))
    projection /= np.linalg.norm(projection, axis=1, keepdims=True)
    return owner, projection


def test_validate_vector_rejects_two_dimensional():
    with pytest.raises(ValueError, match="input must be one-dimensional"):
        validate_vector([[1.0]], 4)


def test_validate_vector_rejects_empty():
    with pytest.raises(ValueError, match="input must not be empty"):
        validate_vector([], 4)


@pytest.mark.parametrize("value", [np.nan, np.inf])
def test_validate_vector_rejects_nan_and_inf(value):
    with pytest.raises(ValueError, match="input contains NaN or infinity"):
        validate_vector([value], 4)


def test_validate_vector_rejects_over_capacity():
    with pytest.raises(ValueError, match="input length 5 exceeds slot capacity 4"):
        validate_vector(np.ones(5), 4)


def test_validate_projection_rejects_one_dimensional():
    with pytest.raises(ValueError, match="projection must be two-dimensional"):
        validate_projection([1.0, 2.0])


def test_parameters_slot_count_and_validation():
    assert CKKSParameters().slot_count == 4096
    with pytest.raises(ValueError, match="poly_modulus_degree must be 8192 or 16384"):
        CKKSParameters(poly_modulus_degree=1000).validate()


def test_data_owner_requires_tenseal(monkeypatch):
    monkeypatch.setattr(split_roles, "TENSEAL_AVAILABLE", False)
    with pytest.raises(FHEUnavailableError, match="TenSEAL is required"):
        DataOwner()


def test_evaluator_source_never_decrypts():
    assert ".decrypt(" not in inspect.getsource(Evaluator)


def test_round_trip_matches_plaintext_reference():
    pytest.importorskip("tenseal")
    assert split_roles.run_split_roles_demo(64, 8, seed=3)["max_abs_error"] < 1e-3


def test_public_context_has_no_secret_key(owner_and_projection):
    ts = pytest.importorskip("tenseal")
    owner, _ = owner_and_projection
    assert ts.context_from(owner.public_context()).is_private() is False


def test_evaluator_rejects_private_context(owner_and_projection):
    pytest.importorskip("tenseal")
    owner, projection = owner_and_projection
    # TenSEAL excludes secret keys by default, so include one explicitly here.
    private_context = owner._context.serialize(save_secret_key=True)
    with pytest.raises(KeyBoundaryError, match="must not contain a secret key"):
        Evaluator(private_context, projection)


def test_evaluator_runs_without_decrypt(owner_and_projection, monkeypatch):
    ts = pytest.importorskip("tenseal")
    owner, projection = owner_and_projection
    encrypted = owner.encrypt(np.random.default_rng(1).standard_normal(64))

    def reject_decrypt(*args, **kwargs):
        raise AssertionError("decrypt called by evaluator")

    monkeypatch.setattr(ts.CKKSVector, "decrypt", reject_decrypt)
    features = Evaluator(owner.public_context(), projection).evaluate(encrypted)
    assert len(features.ciphertexts) == 8


def test_evaluator_cannot_decrypt_results(owner_and_projection):
    ts = pytest.importorskip("tenseal")
    owner, projection = owner_and_projection
    features = Evaluator(owner.public_context(), projection).evaluate(owner.encrypt(np.ones(64)))
    public_context = ts.context_from(owner.public_context())
    result = ts.ckks_vector_from(public_context, features.ciphertexts[0])
    with pytest.raises(Exception):
        result.decrypt()


def test_context_mismatch_is_rejected(owner_and_projection):
    pytest.importorskip("tenseal")
    owner, projection = owner_and_projection
    other = DataOwner()
    evaluator = Evaluator(owner.public_context(), projection)
    with pytest.raises(ContextMismatchError, match="different context"):
        evaluator.evaluate(other.encrypt(np.ones(64)))


def test_tampered_ciphertext_is_detected(owner_and_projection):
    pytest.importorskip("tenseal")
    owner, projection = owner_and_projection
    features = Evaluator(owner.public_context(), projection).evaluate(owner.encrypt(np.ones(64)))
    damaged = features.ciphertexts[0][:-1] + bytes([features.ciphertexts[0][-1] ^ 0xFF])
    tampered = replace(features, ciphertexts=(damaged, *features.ciphertexts[1:]))
    with pytest.raises(IntegrityError, match="ciphertext 0 failed its integrity check"):
        owner.decrypt_features(tampered, expected_count=8)


def test_feature_count_mismatch_is_rejected(owner_and_projection):
    pytest.importorskip("tenseal")
    owner, projection = owner_and_projection
    features = Evaluator(owner.public_context(), projection).evaluate(owner.encrypt(np.ones(64)))
    with pytest.raises(ValueError, match="feature count mismatch"):
        owner.decrypt_features(features, expected_count=9)


def test_projection_width_mismatch_is_rejected(owner_and_projection):
    pytest.importorskip("tenseal")
    owner, _ = owner_and_projection
    evaluator = Evaluator(owner.public_context(), np.ones((4, 32)))
    with pytest.raises(ValueError, match="projection width does not match input length"):
        evaluator.evaluate(owner.encrypt(np.ones(64)))
