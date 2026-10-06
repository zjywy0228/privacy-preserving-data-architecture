"""Record how a published result was produced."""

from __future__ import annotations

import importlib.metadata
import platform
import subprocess
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
RUN_MODES = ("measured", "archived_record", "synthetic_fixture", "mock", "illustrative_sample")
DEFAULT_PACKAGES = ("numpy", "tenseal", "torch", "opacus", "PyYAML")


def repo_root() -> Path:
    """Return the repository root resolved from this file's location."""
    return Path(__file__).resolve().parent.parent


def git_commit(root: Path | None = None) -> str | None:
    """Return the current HEAD commit hash, or None when git is unavailable."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root or repo_root(),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    stdout = result.stdout.strip()
    if result.returncode == 0 and stdout:
        return stdout
    return None


def git_is_dirty(root: Path | None = None) -> bool | None:
    """Return True when the working tree has uncommitted changes, None without git."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root or repo_root(),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode == 0:
        return bool(result.stdout.strip())
    return None


def package_versions(names: Sequence[str] = DEFAULT_PACKAGES) -> dict[str, str | None]:
    """Return a mapping of distribution names to installed versions, None when missing."""
    versions: dict[str, str | None] = {}
    for name in names:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return versions


def build_provenance(
    run_mode: str,
    generator: str,
    seed: int | None = None,
    packages: Sequence[str] = DEFAULT_PACKAGES,
    root: Path | None = None,
) -> dict[str, Any]:
    """Return a provenance dict for a published result."""
    if run_mode not in RUN_MODES:
        raise ValueError(f"unknown run_mode {run_mode!r}; expected one of {RUN_MODES}")
    if not generator.strip():
        raise ValueError("generator must name the script that produced the result")
    return {
        "schema_version": SCHEMA_VERSION,
        "run_mode": run_mode,
        "generator": generator,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_commit": git_commit(root),
        "source_dirty": git_is_dirty(root),
        "python_version": platform.python_version(),
        "platform": platform.platform(terse=True),
        "packages": package_versions(packages),
        "seed": seed,
    }
