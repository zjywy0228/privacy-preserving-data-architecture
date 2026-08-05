"""Regression checks for the repository's foundation-paper citations."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".bib", ".csv", ".html", ".md", ".py", ".toml", ".yaml", ".yml"}

# Split the old identifiers so this source file does not contain the exact
# strings that the repository-wide scan is designed to reject.
SUPERSEDED_IDENTIFIERS = (
    "10.3390/" + "app14062531",
    "10.1007/" + "s11063-024-11604-9",
    "10.1109/" + "ACCESS.2025.3527806",
    "10.1038/" + "s43587-024-00783-8",
    'Models," IEEE, ' + "2025",
    "[" + "author list]",
)

EXPECTED_CITATIONS = {
    "10.69987/JACS.2024.40202": (
        "CITATION.md",
        "README.md",
        "docs/papers/references.bib",
    ),
    "10.70393/616a736d.323732": (
        "CITATION.md",
        "README.md",
        "docs/papers/references.bib",
    ),
    "10.70393/6a69656173.323736": (
        "CITATION.md",
        "README.md",
        "docs/papers/references.bib",
    ),
    "10.1038/s43587-025-01005-x": (
        "CITATION.md",
        "CITATIONS-OF-THIS-REPO.md",
        "README.md",
        "README.zh-CN.md",
        "architectures/biomedical-reference-architecture.md",
        "docs/papers/references.bib",
        "docs/papers/metadata-verification.md",
    ),
    "10.1038/s41598-025-30271-3": (
        "CITATION.md",
        "CITATIONS-OF-THIS-REPO.md",
        "README.md",
        "README.zh-CN.md",
        "architectures/biomedical-reference-architecture.md",
        "docs/papers/references.bib",
        "docs/papers/metadata-verification.md",
    ),
}

BIOMEDICAL_ROLE_SCOPE_FILES = (
    "CITATION.md",
    "README.md",
    "architectures/biomedical-reference-architecture.md",
    "docs/papers/metadata-verification.md",
)


def _repository_text_files() -> list[Path]:
    return [
        path
        for path in ROOT.rglob("*")
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES and ".git" not in path.parts
    ]


def test_superseded_anchor_paper_dois_are_absent() -> None:
    findings: list[str] = []
    for path in _repository_text_files():
        text = path.read_text(encoding="utf-8")
        for identifier in SUPERSEDED_IDENTIFIERS:
            if identifier.lower() in text.lower():
                findings.append(f"{path.relative_to(ROOT)}: {identifier}")

    assert not findings, "Superseded citation metadata found:\n" + "\n".join(findings)


def test_verified_dois_are_present_in_canonical_files() -> None:
    missing: list[str] = []
    for doi, relative_paths in EXPECTED_CITATIONS.items():
        for relative_path in relative_paths:
            text = (ROOT / relative_path).read_text(encoding="utf-8")
            if doi.lower() not in text.lower():
                missing.append(f"{relative_path}: {doi}")

    assert not missing, "Verified citation metadata missing:\n" + "\n".join(missing)


def test_biomedical_papers_are_scoped_as_application_context() -> None:
    missing: list[str] = []
    for relative_path in BIOMEDICAL_ROLE_SCOPE_FILES:
        text = (ROOT / relative_path).read_text(encoding="utf-8").lower()
        if "application" not in text or "contribution statement" not in text:
            missing.append(relative_path)

    assert not missing, "Biomedical role boundary missing:\n" + "\n".join(missing)
