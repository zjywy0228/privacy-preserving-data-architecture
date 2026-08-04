"""Tests for the tracked-text public-scope guard."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

from check_public_scope import scan_paths  # noqa: E402


def test_safe_public_text_passes(tmp_path: Path) -> None:
    document = tmp_path / "README.md"
    document.write_text("Reusable privacy-preserving architecture.\n", encoding="utf-8")

    assert scan_paths([document], tmp_path) == []


def test_private_case_term_is_reported_with_line_number(tmp_path: Path) -> None:
    document = tmp_path / "notes.md"
    blocked = "u" + "scis"
    document.write_text(f"public line\n{blocked} material\n", encoding="utf-8")

    hits = scan_paths([document], tmp_path)

    assert len(hits) == 1
    assert hits[0].path == "notes.md"
    assert hits[0].line == 2
    assert hits[0].term == blocked


def test_private_case_term_in_path_is_reported(tmp_path: Path) -> None:
    blocked = "n" + "iw"
    document = tmp_path / f"{blocked}-notes.md"
    document.write_text("technical content\n", encoding="utf-8")

    hits = scan_paths([document], tmp_path)

    assert len(hits) == 1
    assert hits[0].line == 0
