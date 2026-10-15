# Phase 2 — acquisition implementation; actual download blocked

Status: not complete. Official archive verification has not been performed.

## Implemented

- Locked acquisition to the authoritative repository, revision, filename, byte
  count, SHA-256 and license. Configuration cannot silently redefine the source.
- Added official Hugging Face SDK download with public access and no token.
- Added streaming verification, temporary staging and atomic promotion to the
  read-only final raw archive. An existing mismatching file is never replaced.
- Reverify cached bytes on every acquisition call; do not trust a prior receipt.
- Write provenance atomically only after verification, preserving acquisition time
  on repeat verification. A conflicting manifest is not overwritten.
- Leave actual row count null and schema validation false until Phase 3.
- Updated CLI, README, phase checklist and INTERVIEW.md.

## Verification evidence

`make check`: lint/format pass; 23 tests pass (14 acquisition tests and 9 scaffold
checks). Fixtures exercise success and reuse, truncated/same-size corruption,
wrong filenames, changed source identity, conflicting receipts, official SDK
arguments and network failures. Tests never download the full dataset.

An actual request to the pinned official URL failed with HTTP 403 from the
configured proxy. The current restricted policy does not allow huggingface.co.
Enable that domain and the storage hosts reached by its redirects using the
cloud environment network settings, then run `make acquire`.

Expected archive: 311,422,618 bytes, SHA-256
`2716e1bf0fd157a93b5bf86924d9088419dfbac2022c6cd90030220634f616dc`.
These are expected values, not measured download results.

No actual row count, schema audit, splits, models or holdout evaluation have been
produced. Phase 3 remains gated on successful acquisition and user approval of
Phase 2 completion.
