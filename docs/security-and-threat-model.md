# Security, privacy, and threat model

The local vertical is designed for consented mock sessions and is not a production security boundary. The candidate client shows a recording indicator, the API requires consent, telemetry signatures use per-session keys, stale timestamps are rejected, and nonces are single-use in the current process. A restart-safe nonce store, authentication, authorization, CSRF protection, rate limits, managed key storage, encrypted database fields, and separate biometric-template storage remain deployment work.

## Threats

A malicious operator could use covert capture, infer sensitive behavior, retain recordings indefinitely, or use automated flags as an unattended decision. The system must therefore require written consent, show capture status, restrict participants to enrolled consenting adults, minimize non-candidate transcription, encrypt media and biometric material, apply retention deletion, and require human review.

## Retention

`services.api.privacy.delete_expired_files` provides deterministic deletion for configured directories. It must be invoked by a protected scheduled worker in deployment. The local API does not yet expose an unauthenticated deletion endpoint.

## Encryption

`EncryptedMediaStore` uses Fernet when the optional `cryptography` package is installed. Production key storage must use a managed secret/KMS. The default local SQLite/media path is not encrypted and must not contain real participant material.
