# Project Tasks

Last updated: 2026-08-03

This is the public engineering task tracker for the repository. An item is
checked only after the implementation and its relevant tests or documentation
checks are complete.

## Repository integrity and release readiness

- [x] Add a public task tracker and ignore local coverage artifacts.
- [x] Correct the three anchor papers' venue, author, page, and DOI metadata
  everywhere in the repository.
- [x] Add an automated GitHub Release workflow for version tags.
- [ ] Publish the `v0.3.0` tag and GitHub Release.
- [x] Add a regression test that rejects the superseded citation metadata.

## Architecture and validation

- [ ] Add threat models for the FHE, differential-privacy, and LLM-leakage
  workstreams.
- [ ] Add a federated FHE reference extension with mock-safe tests.
- [ ] Add a privacy-budget visualization tool with deterministic test output.
- [ ] Add an automated LLM leakage-assessment report generator.
- [ ] Add a streaming FHE pipeline for chunked large-input processing.
- [ ] Add adaptive clipping for differential-private training.

## Governance and standards

- [ ] Merge the governed data-access control policy template.
- [ ] Reconcile the NIST Privacy Framework 1.1 mapping with its current
  publication status and implemented repository modules.
- [ ] Add a machine-readable validation report for compliance mappings.

## Quality gates

- [x] Maintain a passing Python 3.10-3.12 continuous-integration matrix.
- [x] Maintain at least 65% automated test coverage in continuous integration.
- [x] Validate the NIST control-mapping CSV in continuous integration.
- [x] Add citation-integrity checks to continuous integration.
- [ ] Add a dependency security audit and documented remediation workflow.

## Later enhancements

- [ ] Extend the synthetic clinical generator with multimodal metadata.
- [ ] Add benchmark-regression checks for FHE throughput.
- [ ] Add real-time leakage assessment for streaming inference.
- [ ] Perform a full documentation link and version audit.
