"""
Unit tests for fhe-feature-extraction/fhe_pipeline.py
======================================================
All 8 tests run in mock mode (no TenSEAL required).  We patch
fhe_pipeline.TENSEAL_AVAILABLE to False before constructing any objects so that
the real tenseal library is never imported.

Run with:
    python -m pytest tests/test_fhe_pipeline.py -v
or:
    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

# ---------------------------------------------------------------------------
# Make sure fhe_pipeline is importable by inserting its parent directory.
# ---------------------------------------------------------------------------
_FHE_DIR = Path(__file__).resolve().parent.parent / "fhe-feature-extraction"
if str(_FHE_DIR) not in sys.path:
    sys.path.insert(0, str(_FHE_DIR))

import fhe_pipeline  # noqa: E402

# ---------------------------------------------------------------------------
# Helper: build objects with TENSEAL_AVAILABLE forced to False
# ---------------------------------------------------------------------------


def _make_context() -> fhe_pipeline.FHEContext:
    """Return an FHEContext operating in mock mode."""
    with mock.patch.object(fhe_pipeline, "TENSEAL_AVAILABLE", False):
        return fhe_pipeline.FHEContext()


def _make_extractor(
    input_dim: int = 64,
    feature_dim: int = 16,
    ctx: fhe_pipeline.FHEContext | None = None,
) -> fhe_pipeline.FHEFeatureExtractor:
    """Build an FHEFeatureExtractor in mock mode with a known-good projection matrix.

    fhe_pipeline uses np.linalg.svd(..., full_matrices=False) and assigns U as W.
    When feature_dim < input_dim, U.shape == (feature_dim, feature_dim), not
    (feature_dim, input_dim), which breaks dot products.  We always supply an
    explicit projection_matrix so that code path is bypassed entirely.
    """
    ctx = ctx or _make_context()
    # Build a well-shaped projection matrix (rows are unit vectors).
    rng = np.random.default_rng(0)
    W = rng.standard_normal((feature_dim, input_dim))
    W /= np.linalg.norm(W, axis=1, keepdims=True)  # normalise rows
    with mock.patch.object(fhe_pipeline, "TENSEAL_AVAILABLE", False):
        return fhe_pipeline.FHEFeatureExtractor(
            input_dim=input_dim,
            feature_dim=feature_dim,
            fhe_context=ctx,
            projection_matrix=W,
        )


def _make_pipeline(
    input_dim: int = 64,
    feature_dim: int = 16,
) -> fhe_pipeline.DataMinimizationPipeline:
    extractor = _make_extractor(input_dim=input_dim, feature_dim=feature_dim)
    return fhe_pipeline.DataMinimizationPipeline(extractor)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestFHEContextMockMode(unittest.TestCase):
    def test_mock_context_encrypt_returns_mock_vector(self):
        """FHEContext without TenSEAL must return _MockEncryptedVector."""
        ctx = _make_context()
        vec = np.array([1.0, 2.0, 3.0])
        with mock.patch.object(fhe_pipeline, "TENSEAL_AVAILABLE", False):
            enc = ctx.encrypt_vector(vec)
        self.assertIsInstance(enc, fhe_pipeline._MockEncryptedVector)


class TestMockEncryptedVector(unittest.TestCase):
    def _mock(self, data: list) -> fhe_pipeline._MockEncryptedVector:
        return fhe_pipeline._MockEncryptedVector(np.array(data, dtype=float))

    def test_mock_vector_add(self):
        """_MockEncryptedVector __add__ should element-wise add two mock vectors."""
        a = self._mock([1.0, 2.0, 3.0])
        b = self._mock([4.0, 5.0, 6.0])
        result = a + b
        self.assertIsInstance(result, fhe_pipeline._MockEncryptedVector)
        np.testing.assert_array_almost_equal(result._data, [5.0, 7.0, 9.0])

    def test_mock_vector_mul(self):
        """_MockEncryptedVector __mul__ scalar should scale every element."""
        a = self._mock([1.0, 2.0, 4.0])
        result = a * 3.0
        self.assertIsInstance(result, fhe_pipeline._MockEncryptedVector)
        np.testing.assert_array_almost_equal(result._data, [3.0, 6.0, 12.0])


class TestFHEFeatureExtractor(unittest.TestCase):
    def test_extractor_output_shape(self):
        """extract() returns a 2-tuple; decrypt_features gives a feature_dim array."""
        input_dim, feature_dim = 64, 16
        extractor = _make_extractor(input_dim=input_dim, feature_dim=feature_dim)
        vec = np.random.default_rng(0).standard_normal(input_dim)

        with mock.patch.object(fhe_pipeline, "TENSEAL_AVAILABLE", False):
            result = extractor.extract(vec)

        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

        enc_input, enc_features = result
        with mock.patch.object(fhe_pipeline, "TENSEAL_AVAILABLE", False):
            features = extractor.decrypt_features(enc_features)

        self.assertEqual(features.shape, (feature_dim,))

    def test_extractor_custom_projection(self):
        """A custom projection_matrix passed at construction should be stored as W."""
        input_dim, feature_dim = 8, 4
        W = np.eye(feature_dim, input_dim)  # deterministic, non-random
        _extractor = _make_extractor(input_dim=input_dim, feature_dim=feature_dim)
        # Re-build with an explicit projection matrix.
        ctx = _make_context()
        with mock.patch.object(fhe_pipeline, "TENSEAL_AVAILABLE", False):
            extractor_custom = fhe_pipeline.FHEFeatureExtractor(
                input_dim=input_dim,
                feature_dim=feature_dim,
                fhe_context=ctx,
                projection_matrix=W,
            )
        np.testing.assert_array_equal(extractor_custom.W, W)


class TestDataMinimizationPipeline(unittest.TestCase):
    def _run_pipeline(
        self,
        pipeline: fhe_pipeline.DataMinimizationPipeline,
        input_dim: int = 64,
        n: int = 1,
    ) -> list:
        rng = np.random.default_rng(99)
        features_list = []
        for i in range(n):
            vec = rng.standard_normal(input_dim)
            with mock.patch.object(fhe_pipeline, "TENSEAL_AVAILABLE", False):
                features = pipeline.process(
                    data_id=f"rec-{i:03d}",
                    plaintext_input=vec,
                    requester="test_suite",
                    purpose="unit-test",
                )
            features_list.append(features)
        return features_list

    def test_pipeline_process_returns_features(self):
        """DataMinimizationPipeline.process() must return a numpy array."""
        pipeline = _make_pipeline(input_dim=64, feature_dim=16)
        results = self._run_pipeline(pipeline, input_dim=64, n=1)
        self.assertIsInstance(results[0], np.ndarray)

    def test_pipeline_audit_log_grows(self):
        """After N process() calls the audit log must have exactly N entries."""
        n = 5
        pipeline = _make_pipeline(input_dim=64, feature_dim=16)
        self._run_pipeline(pipeline, input_dim=64, n=n)
        self.assertEqual(len(pipeline.get_audit_log()), n)

    def test_pipeline_audit_log_no_raw_data(self):
        """Every audit entry must have raw_data_returned == False."""
        pipeline = _make_pipeline(input_dim=64, feature_dim=16)
        self._run_pipeline(pipeline, input_dim=64, n=3)
        for entry in pipeline.get_audit_log():
            self.assertIn("raw_data_returned", entry)
            self.assertFalse(entry["raw_data_returned"])


class TestFHEContextDecryptDirect(unittest.TestCase):
    """Covers FHEContext.decrypt_vector branches (lines 83-86 in mock mode)."""

    def test_decrypt_mock_vector_returns_original(self):
        """decrypt_vector on a _MockEncryptedVector must return the original data."""
        ctx = _make_context()
        original = np.array([1.5, -2.3, 0.7])
        mock_enc = fhe_pipeline._MockEncryptedVector(original)
        with mock.patch.object(fhe_pipeline, "TENSEAL_AVAILABLE", False):
            result = ctx.decrypt_vector(mock_enc)
        np.testing.assert_array_almost_equal(result, original)

    def test_decrypt_unrecognised_type_raises(self):
        """decrypt_vector must raise ValueError for an unknown encrypted type."""
        ctx = _make_context()
        with mock.patch.object(fhe_pipeline, "TENSEAL_AVAILABLE", False):
            with self.assertRaises(ValueError):
                ctx.decrypt_vector("not_a_vector")


class TestMockEncryptedVectorScalarAdd(unittest.TestCase):
    """Covers _MockEncryptedVector.__add__ with a non-mock scalar (line 98)."""

    def test_add_plain_scalar(self):
        """Adding a plain float to a MockEncryptedVector must broadcast correctly."""
        enc = fhe_pipeline._MockEncryptedVector(np.array([1.0, 2.0, 3.0]))
        result = enc + 10.0
        self.assertIsInstance(result, fhe_pipeline._MockEncryptedVector)
        np.testing.assert_array_almost_equal(result._data, [11.0, 12.0, 13.0])

    def test_add_plain_array(self):
        """Adding a plain numpy array must element-wise add without wrapping."""
        enc = fhe_pipeline._MockEncryptedVector(np.array([1.0, 2.0, 3.0]))
        result = enc + np.array([10.0, 20.0, 30.0])
        self.assertIsInstance(result, fhe_pipeline._MockEncryptedVector)
        np.testing.assert_array_almost_equal(result._data, [11.0, 22.0, 33.0])


class TestFHEFeatureExtractorAutoProjection(unittest.TestCase):
    """Covers lines 145-148: auto-generated orthogonal projection matrix."""

    def test_auto_projection_shape(self):
        """Extractor built without projection_matrix must produce W with correct shape."""
        input_dim, feature_dim = 32, 8
        ctx = _make_context()
        with mock.patch.object(fhe_pipeline, "TENSEAL_AVAILABLE", False):
            extractor = fhe_pipeline.FHEFeatureExtractor(
                input_dim=input_dim,
                feature_dim=feature_dim,
                fhe_context=ctx,
                projection_matrix=None,  # triggers auto-generation
            )
        self.assertEqual(extractor.W.shape, (feature_dim, input_dim))

    def test_auto_projection_rows_approx_orthonormal(self):
        """Auto-generated rows must be approximately orthonormal (SVD gives unit rows)."""
        ctx = _make_context()
        with mock.patch.object(fhe_pipeline, "TENSEAL_AVAILABLE", False):
            extractor = fhe_pipeline.FHEFeatureExtractor(
                input_dim=16,
                feature_dim=4,
                fhe_context=ctx,
            )
        norms = np.linalg.norm(extractor.W, axis=1)
        np.testing.assert_array_almost_equal(norms, np.ones(4), decimal=5)

    def test_auto_projection_extract_runs(self):
        """Extractor with auto projection must still process inputs end-to-end."""
        input_dim, feature_dim = 32, 8
        ctx = _make_context()
        with mock.patch.object(fhe_pipeline, "TENSEAL_AVAILABLE", False):
            extractor = fhe_pipeline.FHEFeatureExtractor(
                input_dim=input_dim,
                feature_dim=feature_dim,
                fhe_context=ctx,
            )
        vec = np.random.default_rng(7).standard_normal(input_dim)
        with mock.patch.object(fhe_pipeline, "TENSEAL_AVAILABLE", False):
            _, enc_features = extractor.extract(vec)
            features = extractor.decrypt_features(enc_features)
        self.assertEqual(features.shape, (feature_dim,))


class TestFHEFeatureExtractorShapeValidation(unittest.TestCase):
    """Covers the assertion in FHEFeatureExtractor.__init__ and extract()."""

    def test_wrong_projection_shape_raises(self):
        """Passing a projection_matrix with wrong shape must raise AssertionError."""
        ctx = _make_context()
        with mock.patch.object(fhe_pipeline, "TENSEAL_AVAILABLE", False):
            with self.assertRaises(AssertionError):
                fhe_pipeline.FHEFeatureExtractor(
                    input_dim=16,
                    feature_dim=4,
                    fhe_context=ctx,
                    projection_matrix=np.eye(5, 16),  # wrong: (5, 16) not (4, 16)
                )

    def test_wrong_input_shape_raises(self):
        """Passing input with wrong length to extract() must raise AssertionError."""
        extractor = _make_extractor(input_dim=64, feature_dim=16)
        bad_vec = np.ones(32)  # wrong dimension
        with mock.patch.object(fhe_pipeline, "TENSEAL_AVAILABLE", False):
            with self.assertRaises(AssertionError):
                extractor.extract(bad_vec)


if __name__ == "__main__":
    unittest.main()
