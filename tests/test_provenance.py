"""Tests for the tools/provenance.py helper."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import provenance  # noqa: E402
from provenance import build_provenance, git_commit, git_is_dirty, package_versions  # noqa: E402

EXPECTED_KEYS = {
    "schema_version",
    "run_mode",
    "generator",
    "generated_at",
    "source_commit",
    "source_dirty",
    "python_version",
    "platform",
    "packages",
    "seed",
}


def test_build_provenance_contains_required_keys() -> None:
    """A build_provenance call produces exactly the ten documented keys."""
    result = build_provenance("mock", "tests/test_provenance.py", seed=3)
    assert set(result.keys()) == EXPECTED_KEYS
    assert len(EXPECTED_KEYS) == 10
    assert result["seed"] == 3
    assert result["run_mode"] == "mock"


def test_unknown_run_mode_raises() -> None:
    """build_provenance rejects an unknown run_mode."""
    with pytest.raises(ValueError, match="unknown run_mode"):
        build_provenance("guess", "x")


def test_empty_generator_raises() -> None:
    """build_provenance rejects a blank generator string."""
    with pytest.raises(ValueError):
        build_provenance("mock", "   ")


def test_git_helpers_return_none_without_git(monkeypatch: pytest.MonkeyPatch) -> None:
    """Both git helpers return None when subprocess.run raises FileNotFoundError."""

    def _raise(*_args: object, **_kwargs: object) -> None:
        raise FileNotFoundError("git not installed")

    monkeypatch.setattr(provenance.subprocess, "run", _raise)
    assert git_commit() is None
    assert git_is_dirty() is None


def test_missing_package_version_is_none() -> None:
    """package_versions reports None for a package that is not installed."""
    assert package_versions(("definitely-not-installed-package-xyz",)) == {
        "definitely-not-installed-package-xyz": None,
    }


def test_generated_at_is_utc_iso() -> None:
    """generated_at parses as a timezone-aware ISO timestamp at UTC."""
    result = build_provenance("mock", "tests/test_provenance.py")
    parsed = datetime.fromisoformat(result["generated_at"])
    assert parsed.utcoffset() == timedelta(0)
