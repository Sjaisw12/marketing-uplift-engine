# Phase 2 — dataset acquisition completion evidence

Implementation and acquisition are complete; user review and approval are pending.
Scope follows AGENTS.md, docs/PHASES.md, and the explicit Phase 2 authorization.
The authoritative roadmap PDF was not available in mounted project files for
independent comparison. No later phase was implemented or executed.

## Verified source

- Repository: `criteo/criteo-uplift`.
- Revision: `82811785048bb633de2d55c02bab4e57066e6423`.
- Basename: `criteo-research-uplift-v2.1.csv.gz`.
- Download: successful via inherited proxy, HTTPS with TLS verification enabled.
- Observed destination chain: `huggingface.co` → `us.aws.cdn.hf.co`.
- Actual compressed bytes: **311,422,618**, exactly matching configuration.
- Actual SHA-256: `2716e1bf0fd157a93b5bf86924d9088419dfbac2022c6cd90030220634f616dc`.
- Independent `stat` and `sha256sum` confirmed the acquisition implementation's results.
- Expected rows: **13,979,592**. Observed rows: **not measured**.
- `data/manifest.json` records successful compressed-byte verification and provenance.

The command downloads to a unique temporary file, verifies disk bytes, then
atomically replaces the final archive. Short, oversized, interrupted, or corrupt
downloads fail and partial files are removed. Existing archives are rehashed;
invalid existing files fail rather than being silently replaced. The manifest is
published atomically only after successful verification. It is historical evidence
and must not substitute for rechecking current files.

## Verification

`make check` passed: Ruff lint, Ruff formatting, and **21 pytest tests** on
Python 3.12.14. The 12 acquisition cases cover successful acquisition/provenance,
reuse and detection of subsequently corrupted bytes, short downloads, same-size
checksum corruption, oversized downloads, interrupted responses after partial
writes, sanitized HTTP 403/DNS/proxy errors, insufficient disk, wrong basename,
and CLI dispatch. The nine scaffold checks retain the later phase gates.
`make status` succeeds and identifies all later stages as reserved.

The actual archive and a representative partial-file path were confirmed ignored
by Git. No dataset, credentials, or large files were uploaded or committed.

## Storage and environment limitations

Before acquisition, `/workspace` had **32,034,635,776 bytes** free, sufficient for
the 311 MB compressed archive. No decompression was performed. The archive is local
to this workspace; persistence into new Codex Cloud tasks/environments is not
established and must not be assumed. Git carries only code and small provenance.
A fresh workspace should rerun `make acquire`; restored files are always rehashed.
No durable external dataset storage was configured.

A direct `uv` invocation first failed because its default home cache was read-only;
the repository already specifies a writable `.cache/uv` location. `make check`
initially failed to fetch build dependency `setuptools==80.9.0` from `pypi.org`
with `Operation not permitted (os error 1)` in the command sandbox. Running with
command network access enabled and the existing repository cache configuration
succeeded. The actual dataset download then succeeded without a transfer error.
No persistent environment, proxy, or allowlist changes were made.

## Review and next gate

Review the acquisition module, CLI routing, tests, manifest, README, checklist,
Makefile comment, and interview notes. `make acquire` re-verifies existing bytes;
`make check` runs offline fixture tests once the locked environment is installed.
Phase 3 validation, ingestion, Parquet conversion, partitions, exploratory analysis,
and modeling remain unimplemented and require separate approval.
