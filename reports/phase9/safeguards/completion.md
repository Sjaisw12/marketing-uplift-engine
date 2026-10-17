# Stage B safeguards preparation completion

Base: e5ae9774513c12f168288524255457631286452c. Branch: codex/phase-9-execution-safeguards.

Execution-lock SHA-256: `2792d14576f1b3a84acad042c2f22f28693e875e52cba795ddb98385fb3e758a` (64 bound files).
Stage A lock: `fbd0ec32f8d97bbc1ffe03dd4a16a7937390d4ac570becef83b109cbc3d32b93`.
Unchanged model-manifest SHA-256: `2e91bdae68cad12604c6aff3a9337b62e40df383f1ce6b2d3d4c1c58e08b8c9e`.

## Actual verification

- `make check`: 212 passed, 18 full-data tests deselected, 14.10s. Ruff lint and formatting passed (67 Python files).
- 47 new safeguard tests are included in that total.
- Permitted Stage A development-only full gate: 1 passed in 12.38s. Nine models reload correctly; original 276 protected entries, frozen memberships, private Stage A provenance and historical MLflow remain unchanged.
- New portable execution lock and unchanged Stage A public lock verify. Relocation, changed-source/settings/parent-lock tests pass.
- RFC8032 Ed25519 reference; synthetic signature/domain/identity/expiry failures; fixed-cohort duplicate/ownership rejection; timeout-after-write stops; local Git two-client create race and persisted receipt read; checkpoint tampering/path checks; journal/crash/recovery and unconditional real-access denial tested.

## What is and is not implemented

Additive verification primitives, a runner-injected create-only Git command adapter,
checkpoint/backup attestation verification, and a hash-chained synthetic state machine
are implemented. Default transport is inert. Real scoring/evaluation always deny.
No real coordinator, persistent production event journal, production signing key,
live ruleset enforcement or independently durable backup is claimed operational.
No holdout record, outcome statistic or final metric was accessed/calculated.
No production receipt, GitHub settings change, live write test, new infrastructure,
credential, paid resource, model refit, dependency change or Phase 10 work.

The private key remains owner-controlled outside Codex/GitHub. Test-generated keys
exist only in synthetic fixtures. No raw records, row-level predictions or model
weights are added to Git. All existing ignored datasets/artifacts remain in place.

## Next gate

Ready for code review and planning an explicitly approved live integration test;
NOT ready for Stage B execution. Follow docs/STAGE_B_SAFEGUARDS.md for exact tag
ruleset settings and proposed disposable namespace. Test actual GitHub initial
creation, duplicate claims, update/deletion denial and fresh-client persistence
only after separate approval. Do not create the real cohort receipt.

Pinning the public key, implementing reviewed live coordination/journal persistence,
and validating backup recovery require a new reviewed execution identity before
separate Stage B approval. Recovery integrity checks never authorize automatic resume.

GitHub refs are not administrator-proof WORM. Local copy hashes cannot prove backup
independence. Future intervals remain nominal conditional working-model estimates;
safeguards do not resolve hidden propensities, release selection or dependence.
