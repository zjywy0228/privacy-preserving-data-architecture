# Contributing to Privacy-Preserving Data Architecture

Thank you for your interest in contributing. This repository implements reusable architecture patterns and prototype modules for privacy-preserving and AI-resilient data analysis. Contributions that improve engineering quality, add verified examples, or extend the architecture coverage are welcome.

---

## Ways to contribute

- **Bug reports and questions:** Open an issue describing the problem, the expected behavior, and any relevant error output.
- **Feature requests:** Open an issue with the use case and the architecture gap it addresses. Reference a relevant federal framework (NIST AI RMF, NIST Privacy Framework, HIPAA, GDPR) if applicable.
- **Code contributions:** Submit a pull request against the `master` branch following the guidelines below.
- **Documentation improvements:** Architecture docs, pattern descriptions, and compliance mappings are as important as code.

---

## Ground rules

1. **No real patient data, no real PHI, no institutional credentials.** All examples must use synthetic or publicly available data. If your demo needs medical-imaging input, use a publicly downloadable synthetic sample.
2. **No references to immigration, USCIS, visa proceedings, or petition strategy anywhere in the repository.** This is an open-source research project; contributions should be scoped to the technical and research content.
3. **Cite real DOIs only.** Do not invent paper references. If you reference a framework control, link to the published document.
4. **Do not delete or rename existing module folders** (`architectures/`, `fhe-feature-extraction/`, `dp-llm-training/`, `llm-leakage-assessment/`, `governance-templates/`, `docs/compliance/`). These names appear in downstream documentation. Add; do not remove.

---

## Code quality

- Python ≥ 3.10. Type hints on all public functions.
- Format with `ruff format`, lint with `ruff check`, type-check with `mypy` before submitting.
- Keep one module under ~400 lines. Split if longer.
- Place tests under `tests/`, mirroring the module path.
- Examples go under `<module>/examples/` and must be runnable with `python <path>` after the documented `pip install`.

---

## Documentation quality

- New modules need a `<module>/README.md` (one page max): purpose, threat model, dependencies, quickstart, and federal-framework alignment.
- Architecture patterns go under `architectures/` with: motivation, scope, components, data-flow diagram (mermaid preferred), federal-alignment table, and references.
- Compliance mappings go under `docs/compliance/` as structured CSV or Markdown tables.

---

## Pull request process

1. Branch from `master` with a descriptive name: `feature/<scope>-<summary>` or `docs/<scope>-<summary>`.
2. Keep the PR focused — one logical change per PR. If you have two independent changes, open two PRs.
3. Run any new code locally and include the output in the PR description.
4. Reference the relevant architecture pattern or compliance control if applicable.
5. The maintainer will review and merge. Solo-repo PRs may self-merge after CI passes.

---

## AI-assisted contributions

This repository is built in an area where AI tooling is both the subject of study and a practical development aid. Contributors who use AI coding tools are encouraged to:

- Review and test all AI-generated code before submitting.
- Add a `Co-authored-by` trailer if an AI tool made substantial contributions to the diff.
- Note any AI-assisted sections in the PR description.

See [`docs/ai-assistance-policy.md`](docs/ai-assistance-policy.md) for how this repository handles AI-assisted development internally.

---

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
