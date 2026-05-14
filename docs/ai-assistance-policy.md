# AI-Assistance Policy

This document describes how AI coding tools are used in this repository and how AI-assisted contributions are reviewed, tested, and disclosed.

---

## Why this document exists

This repository's subject matter is AI data-leakage risk, privacy-preserving computation, and secure data architecture. The `llm-leakage-assessment/` module specifically addresses the risks that AI and large language model tools introduce when they process sensitive data. It would be inconsistent to use AI tools in this repository's development without a policy for how that use is governed.

---

## How AI tools are used here

AI coding tools (such as Claude Code) are used as development aids to:

- Draft boilerplate code structures, type stubs, and docstring outlines.
- Suggest implementations of standard algorithms (e.g., TenSEAL FHE operations, Opacus DP wrappers).
- Assist with documentation drafting, including README sections and architecture descriptions.

AI tools are **not** used as autonomous agents. Every AI-generated contribution is reviewed and tested by the maintainer before commit.

---

## Review and testing requirements

Before any AI-assisted code is committed:

1. The maintainer reads the full diff. AI-generated code is not merged unread.
2. All new Python modules are run locally. Output or test results are included in the PR description.
3. Type hints are verified with `mypy`; formatting with `ruff format`; linting with `ruff check`.
4. Any AI-suggested external library or data dependency is evaluated for size, license, and security posture.

---

## Disclosure in commit history

When AI assistance contributed substantially to a commit, a `Co-authored-by` trailer is added:

```
Co-authored-by: Claude <noreply@anthropic.com>
```

This makes the AI contribution visible in the commit graph without obscuring the maintainer's authorship or review responsibility.

---

## What AI tools do NOT have access to

Consistent with the security principles this repository documents:

- No real patient data, PHI, or institutional datasets are provided to AI tools.
- No credentials, API keys, or access tokens are included in prompts.
- No unpublished research results, pre-publication manuscripts, or proprietary institutional data are shared with AI tools.

---

## Connection to the leakage-assessment module

The `llm-leakage-assessment/` module contains a threat taxonomy and assessment checklist that can be applied to AI-tool workflows. Developers using AI coding tools in security-sensitive contexts are encouraged to run through the relevant sections of the checklist to identify prompt-leakage, log-capture, or context-exfiltration risks before deploying AI tooling in production data environments.

This policy itself was drafted with AI assistance and reviewed by the maintainer before publication.
