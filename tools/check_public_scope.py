"""Reject private-case terminology from tracked public-repository text."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

TEXT_SUFFIXES = {
    ".bib",
    ".css",
    ".csv",
    ".html",
    ".js",
    ".json",
    ".md",
    ".py",
    ".svg",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}

# Split these literals so the guard can scan its own source.
DISALLOWED_TERMS = (
    "n" + "iw",
    "u" + "scis",
    "eb" + "-2",
    "national interest" + " waiver",
    "request for" + " evidence",
    "immigra" + "tion",
)


@dataclass(frozen=True)
class ScopeHit:
    path: str
    line: int
    term: str


def tracked_text_files(repository: Path) -> list[Path]:
    """Return tracked files whose suffix indicates reviewable text."""
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=repository,
        check=True,
        capture_output=True,
    )
    paths = completed.stdout.decode("utf-8").split("\0")
    return [
        repository / path for path in paths if path and Path(path).suffix.lower() in TEXT_SUFFIXES
    ]


def scan_paths(paths: list[Path], repository: Path) -> list[ScopeHit]:
    """Find disallowed terms in relative paths and UTF-8 text content."""
    hits: list[ScopeHit] = []
    for path in paths:
        relative = path.relative_to(repository).as_posix()
        relative_lower = relative.lower()
        for term in DISALLOWED_TERMS:
            if term in relative_lower:
                hits.append(ScopeHit(relative, 0, term))

        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(lines, start=1):
            line_lower = line.lower()
            for term in DISALLOWED_TERMS:
                if term in line_lower:
                    hits.append(ScopeHit(relative, line_number, term))
    return hits


def main() -> int:
    repository = Path(__file__).resolve().parent.parent
    hits = scan_paths(tracked_text_files(repository), repository)
    if not hits:
        print("OK    tracked public text contains no private-case terminology.")
        return 0

    for hit in hits:
        location = f"{hit.path}:{hit.line}" if hit.line else hit.path
        print(f"ERROR {location}: disallowed public-scope term {hit.term!r}", file=sys.stderr)
    print(f"FAIL  found {len(hits)} public-scope violation(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
