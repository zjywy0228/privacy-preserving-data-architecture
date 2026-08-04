# Threat Models

These documents define the security and privacy assumptions for the repository's
three core workstreams:

- [Fully homomorphic encryption feature extraction](fhe-feature-extraction.md)
- [Differential-private training](dp-llm-training.md)
- [Large language model leakage assessment](llm-leakage-assessment.md)

They are implementation guides, not security certifications. Each deploying
organization must repeat the analysis for its own data, identities, network,
key-management system, model provider, and legal obligations.

## Method

Each model records:

1. assets that require protection;
2. trust boundaries and external dependencies;
3. credible threat events;
4. controls implemented in this repository;
5. validation evidence;
6. residual risks and deployment responsibilities.

The threat tables use a combined security/privacy view informed by STRIDE and
LINDDUN. The goal is practical traceability rather than a claim of exhaustive
coverage.

## Shared assumptions

- Examples and tests use synthetic or public data only.
- Raw sensitive data stays inside the data owner's approved environment unless
  a separate, authorized transfer path exists.
- Secrets, encryption keys, credentials, and production datasets are never
  committed to the repository.
- Cryptographic and privacy parameters require workload-specific review.
- Repository prototypes must be integrated with production identity, key
  management, monitoring, incident response, and change-control systems before
  operational use.

## Review cadence

Review the applicable model when:

- a new data type, model provider, or external service is introduced;
- an architecture boundary or key owner changes;
- a new attack class is added to the assessment suite;
- a dependency changes its security model;
- a test or incident reveals an unmodeled failure mode.

Record accepted residual risks in the deploying organization's own risk register.
