# Phase 3 — strict contract, audited Parquet, frozen memberships

Implementation is complete and submitted for review; approval to merge or start
Phase 4 is pending. The full nine-page finalized roadmap was readable. Scope
follows its data-contract and sealed-holdout requirements, AGENTS.md, and the
explicit Phase 3 authorization. Phase 2's completion approval is now checked.

## Actual full-file validation

| Check | Observed result |
| --- | --- |
| Compressed archive bytes | 311,422,618; exact configured match |
| Compressed SHA-256 | `2716e1bf0fd157a93b5bf86924d9088419dfbac2022c6cd90030220634f616dc` |
| Strict independent CSV record count | 13,979,592 |
| Wrong-width records | 0 |
| Typed scan row count | 13,979,592 |
| Raw schema | Exact 16 named columns; original order recorded |
| Missing, unparseable, nonfinite values | 0 in every column |
| Invalid binary indicators | 0 in treatment, visit, conversion, exposure |
| Treatment reference rate | 0.8500001287591226; within [0.84, 0.86] |
| Visit reference rate | 0.046992000911042324; within [0.045, 0.049] |
| Rows dropped / deduplicated; values imputed | 0 / 0; 0 |

These are predeclared mechanical whole-file contract checks, not exploratory
analysis. No arm-specific outcomes, treatment effects, covariate balance,
repeated-vector exploration, model selection, or holdout performance were examined.

`reports/validation.json` contains observed counts and per-column diagnostic counts,
bound to source identity and a contract signature. It survives acquisition reruns;
`data/manifest.json` remains acquisition-only and retains observed rows as null.
Failed validation writes separate diagnostic evidence and stops before ingestion.

## Parquet and deterministic identity

The typed artifact is local `data/processed/criteo-v2.1.parquet`:
**201,099,097 bytes**; SHA-256
`3dd993a074f7346e71d8d99f5ba980990dbf98ec52dfbe3d7848174b04440bd0`.

A zero-based source-record ordinal is assigned during a strict, single-threaded,
order-preserving CSV scan. It is never a customer ID or feature. The canonical
hash packs each ordinal together with all 16 typed values in source order, using
explicit little-endian representations. The validated CSV and complete Parquet
scan both produced:

`26b03f2f2104349ce7693f2179b60b3804886677d42945a359aab196da5e4a8c`

This checks value-to-ID mapping, not merely row count or ID coverage. Raw strings
are diagnostically parsed first; publication uses explicit finite float64 values
and exact 0/1 integer indicators only. No tolerant or failed cast reaches staging.
Repeated anonymous records are preserved. Fixture tests independently build the
canonical bytes in Python, verify batch-size independence, detect ID/value swaps,
and recreate Parquet with identical mapping and bytes.

`select_features` exports exactly f0-f11. Tests reject each forbidden indicator or
row ID. `development_relation` checks frozen memberships and exposes development
records only; it refuses access before all development splits are frozen.

## Sealed holdout and five development re-splits

The holdout was persisted and checked in a distinct command before development
split creation. Seed **20261015**, joint treatment × visit stratification:

| Membership | Actual rows |
| --- | ---: |
| Final holdout | 2,096,939 |
| Development pool | 11,882,653 |
| Training, each repetition | 9,506,122 |
| Validation, each repetition | 2,376,531 |

The development seeds are **104729, 130363, 155921, 181081, 206369**. Each repetition
uses 80/20 splitting within development. Rounding is sklearn's global ceiling of
the test fraction followed by stratified allocation. The registry records versions,
source mapping, seeds, counts, and canonical membership hashes.

Holdout membership SHA-256:
`829efe6744558783321c0dc3addfc60af6b9ba49f31368c89955dce6cdea39fe`.

All **12** memberships (holdout, development, five train/validation pairs) were
recomputed against the real data and matched their frozen hashes. Every pair is
disjoint, completely covers its parent, and excludes holdout IDs from development.
The registry's bytes remained unchanged during reconstruction. Evidence is in
`reports/split_reconstruction.json`; the authoritative frozen definitions are in
`artifacts/splits.json`. Fixture tests additionally delete every local membership
and restore byte-identical files, reject changed seeds/corruption, and require all
hashes to match before restoring any missing file.

Label access was mechanical for predeclared stratification only. No holdout outcome
summaries, scores, or evaluations were generated. Sealing is a tested workflow
boundary, not encryption or OS access control; the immutable staged source still
contains all records. Future analysis must use the development boundary.

## Checks actually run

- Validation component: 16 fixture tests passed and actual full-file validation passed.
- Ingestion component: 25 validation/ingestion fixture tests passed and actual
  source-to-Parquet mapping passed.
- Split component: 30 component fixture tests passed, then the actual holdout and
  development creation/verification commands passed.
- Final `make check`: **50 fast tests passed**, Ruff lint and formatting passed.
- Explicit `pytest -m full_data -q`: **3 full-data tests passed**, covering actual
  source/contract evidence, complete Parquet mapping, and all-membership reconstruction.
- `make status` succeeds; audit, ATE, and baseline commands remain unimplemented.
- `git diff --check` passed. Raw gzip, processed Parquet, and row-level memberships
  are ignored by Git. No dataset or memberships are uploaded.

The full-data workflow now runs on explicit manual dispatch, revalidates cached
archive bytes, ingests, reconstructs against the committed registry, runs real
full-data tests, and uploads only small verification reports. No remote workflow
run is claimed by this report; these results were obtained in Codex Cloud.

## Resources and persistence

The environment has an **8 GiB** cgroup memory ceiling and **two CPUs**. Configuration
uses one DuckDB thread, **2 GB** query memory, a **6 GB** spill ceiling, batches of
65,536 rows, and an **8 GiB free-disk preflight**. Splitting reads only IDs and two
labels and processes one repetition at a time; NumPy/sklearn allocations are in
addition to DuckDB's memory setting. Execution completed within the environment.

The archive uses 311,422,618 bytes, Parquet uses 201,099,097 bytes, and local
membership files total **587,144,392 bytes**. Approximately 29 GiB remained free
after creation. No expanded CSV or full pandas dataframe was materialized.

These local files are not guaranteed to persist into new cloud tasks. Given the
versioned registry, a fresh environment should run acquisition, full validation,
ingestion, and `uplift split --reconstruct`. Source-row mapping and every membership
must match the frozen hashes. A mismatch stops for review; no replacement holdout
or new split seed is authorized. Code, registry, and small reports belong in Git.
