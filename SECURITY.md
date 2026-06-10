# Security Policy

## Supported Versions

This repository contains research prototype code. Only the `master` branch is
actively maintained.

| Branch / tag | Supported |
|---|---|
| `master` | Yes |
| Older tags | No — update to `master` |

## Scope

This repository does **not** process real patient data, credentials, or production
secrets. All examples use synthetic or public-domain data only (see `CONTRIBUTING.md`).

Security reports are most relevant for:

- Vulnerabilities in the FHE pipeline (`fhe-feature-extraction/fhe_pipeline.py`) that
  could silently weaken encryption guarantees
- Differential-privacy budget accounting errors in `dp-llm-training/budget_accountant.py`
  that could over-report privacy guarantees
- Prompt-injection or leakage vectors in `llm-leakage-assessment/assessment_runner.py`
  that the threat taxonomy does not yet cover
- Dependency vulnerabilities in `pyproject.toml` or `requirements-dev.txt`

## Reporting a Vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

Report privately by emailing **zjywy0228@gmail.com** with:

1. A short description of the vulnerability
2. Steps to reproduce or a minimal proof of concept
3. Your assessment of severity and impact
4. Any suggested fix, if you have one

You will receive an acknowledgement within **5 business days**. If the issue is
confirmed, a patch will be prioritized and you will be credited in the release notes
(unless you prefer to remain anonymous).

## Disclosure Policy

- Confirmed vulnerabilities will be patched before public disclosure.
- The fix will be released as a patch commit on `master` with a note in `CHANGELOG.md`.
- For critical issues, a GitHub Security Advisory may be published after patching.
