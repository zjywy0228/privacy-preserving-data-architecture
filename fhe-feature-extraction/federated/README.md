# Federated FHE Extension

This extension coordinates cross-silo updates as opaque serialized fully
homomorphic encryption (FHE) ciphertext. It is designed for Flower-compatible
transport without converting an update to a NumPy array or plaintext on the
aggregation server.

## Data path

1. Each authorized client computes its local update inside its own data
   environment.
2. The client encrypts the vector with a shared public TenSEAL CKKS context.
3. `to_flower_parameters()` wraps the serialized ciphertext as one Flower
   `Parameters` tensor with type `fhe.ckks.serialized.v1`.
4. The server extracts bytes with `from_flower_parameters()` and submits an
   `EncryptedUpdate` to `FederatedFHECoordinator`.
5. `TenSEALCKKSBackend` adds and scales ciphertext vectors without holding the
   secret key.
6. An authorized decryptor receives the aggregated ciphertext and performs the
   separate output-review process.

## Installation

```bash
pip install -e ".[federated]"
```

The `federated` extra installs Flower and TenSEAL. Core tests do not require
either package.

## Audit behavior

The coordinator records:

- round and authorized client identifier;
- ciphertext byte length;
- SHA-256 fingerprint of each received ciphertext and aggregate;
- receipt timestamp.

It does not copy ciphertext payloads, plaintext vectors, secret keys, or local
training data into its audit log.

## Mock backend warning

`MockVectorBackend` is visibly prefixed `MOCK-NOT-ENCRYPTED` and exists only for
continuous integration and examples. It provides no confidentiality and must
never be used with sensitive data.

## Deployment responsibilities

The reference extension does not provide client identity, transport security,
key lifecycle management, replay protection across processes, durable audit-log
storage, or institutional authorization. Production deployments must supply
those controls and verify current Flower/TenSEAL security guidance.
