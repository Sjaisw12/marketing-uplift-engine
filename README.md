# Marketing Uplift & Causal Decision Engine

An offline decision analysis of **incremental visits** under randomized advertising
assignment in the corrected Criteo Uplift v2.1 release. Estimates describe the
released benchmark population, with uncertainty; they do not measure realized
revenue, advertiser-wide lift, or production impact.

## Current state

Phase 3 implements full-file contract validation, audited typed Parquet, a sealed
15% holdout, and five frozen development train/validation splits. Execution evidence
lives in `reports/validation.json`, `reports/ingestion.json`,
`reports/split_reconstruction.json`, and `artifacts/splits.json`. No exploratory
analysis, treatment effects, or models have been run. Later stages remain gated.

## Setup and verification

Use Python 3.11 or 3.12 on Linux. Python 3.12 is the default. Install
[uv 0.12.23](https://github.com/astral-sh/uv/releases/tag/0.12.23), then from the repo root:

```sh
make setup
make check
make status
```

`uv.lock` pins the complete dependency resolution and distribution hashes;
`uv sync --locked` refuses stale project metadata. CI checks both Python versions.
Make targets default to a repository-local, gitignored `.cache/uv` cache; override
`UV_CACHE_DIR` if needed. LightGBM requires an OpenMP runtime (on Debian/Ubuntu, `libgomp1`).

## Commands and approval gates

| Command | Purpose | Implementation phase |
| --- | --- | --- |
| `make status` | Display protocol and available commands | 1, available |
| `make acquire` | Download pinned gzip, verify bytes and SHA-256, write provenance | 2, available |
| `make validate` | Data contract validation | 3, available |
| `uv run --locked uplift validate --full` | Expensive full-file contract stage | 3, available |
| `make ingest` | Audited typed Parquet | 3, available |
| `make split` | Seal final holdout once and freeze five development re-splits | 3, available |
| `make audit` | Development EDA | 4 |
| `make ate` | Development ATE with 95% CI | 5 |
| `make baselines` | Random, visit propensity, S-learner; MLflow logs | 6 |
| `make reproduce` | Sequential rerun entry point, available after implementation | 2–6 |

`make reproduce` currently stops at the unimplemented audit gate. It will
never authorize a final holdout evaluation. Reruns must reuse frozen split files.
Work proceeds by completed checklist and explicit phase approval, without calendar
scheduling or effort estimates. See [phase checklists](docs/PHASES.md).

## Layout and declared protocol

- `src/marketing_uplift/`: package and command interface.
- `configs/project.toml`: source identity, schema, experiment protocol and local tracking.
- `tests/`: fast checks; future full-data tests use the `full_data` marker.
- `data/raw/`, `data/processed/`: ignored data; `data/manifest.json` will record acquisition.
- `reports/`: human-readable audit and results; no row-level exports.
- `artifacts/`: future split registry and local row-level/model artifacts.
- `mlruns/`: ignored local MLflow file store; resolve to an absolute `file://` URI.
- `app/`: future dashboard; no implementation in this phase.

The holdout is 15%, stratified jointly by treatment and visit, with seed 20261015.
Within the remaining 85%, five 80/20 train/validation re-splits use fixed seeds
104729, 130363, 155921, 181081, and 206369. The executed registry in
`artifacts/splits.json` records actual membership hashes and seeds; configuration
alone remains insufficient evidence of frozen partitions.

Features are exclusively `f0`–`f11`. Exposure is post-assignment. Treatment, visit,
and conversion are excluded from exported `X`. The S-learner receives treatment
separately as its intervention indicator, as required by the authoritative roadmap.
The primary outcome is visit; conversion is reserved for V2.

The full-data CI job is enabled on explicit manual workflow dispatch. It caches
only archive bytes by expected digest, then runs full validation, ingestion,
reconstruction of the committed split registry, and real full-data pytest checks.
Only small verification reports are uploaded. Cheap fixture checks run on every
PR without downloading data. A local run is not evidence of a remote CI run.

## Acquisition and cloud storage

Run `make acquire` with network access enabled. It uses the inherited HTTPS proxy
and normal TLS verification, downloads the pinned revision to a unique temporary
file in `data/raw/`, and verifies actual on-disk byte count and SHA-256 before
atomically publishing the archive. A failed or incomplete download is removed;
no automatic retry, resume, or source substitution occurs. An existing archive is
always rehashed; a corrupt existing file fails and requires explicit intervention.
The command checks available disk space before a new download.

`data/manifest.json` records the last successful compressed-byte verification,
source revision, canonical URL, expected and observed size/digest, UTC verification
time, and destination hosts for downloads. Signed redirect URLs are never saved.
Expected rows are 13,979,592; acquisition leaves observed rows `null`. Measured
rows are recorded separately by validation. The manifest is historical provenance, not a live guarantee that local bytes have
not subsequently changed. Run `make acquire` to verify them again.

Raw data and partial files are Git-ignored. A fresh Codex Cloud task/environment
must not assume these local files persist: Git carries code and the small manifest,
not the archive. Reacquire and verify bytes in a new workspace. Durable external
storage or a cache would need a separate, approved arrangement. No external
archive storage has been configured by this phase.

## Phase 3: validation, ingestion, and frozen memberships

Run `make validate`, then `make ingest`, then `make split`. `make validate` performs
full-file validation; direct `uplift validate` requires `--full` so a sampled scan
cannot be reported as a complete contract pass. Rerun the fast checks with
`make check`; run full-data integration checks with
`UV_CACHE_DIR=.cache/uv uv run --locked pytest -m full_data` after the artifacts exist.

Validation independently counts strict CSV records and field widths, checks the
exact 16-column schema, row count, finite numeric features, exact binary values,
and configured treatment/visit reference bands. Failures produce small diagnostic
artifacts under `reports/contract_failures/` and stop. No raw records are printed.
Numeric conversion is explicitly finite float64 parsing for f0-f11 and exact 0/1
integer parsing for the four indicators; no tolerant casts enter the final data.
There is no imputation, filtering, or deduplication.

Source identity is a zero-based CSV data-record ordinal, **not a user ID**. A
single-threaded, order-preserving scan assigns it once. A canonical SHA-256 hashes
every row ID and every typed value in source order. The Parquet mapping must match
that source hash; identifiers alone or row counts alone are insufficient evidence.
Typed staging retains exposure and outcomes, while `select_features` exports only
f0-f11 and asserts the feature boundary. `development_relation` provides the default
analysis access path and excludes the holdout using verified frozen membership.
The staged source still contains all records; sealing is a workflow boundary,
not operating-system access control or encryption.

`data/manifest.json` remains acquisition-only historical evidence. It deliberately
keeps observed rows `null`. **Observed full-file rows and quality results are
recorded separately in `reports/validation.json`**, bound to the source digest and
contract signature. Acquisition reruns cannot erase this evidence. The ingestion
report binds Parquet bytes to that validated source-row mapping. Historical reports
must not substitute for checks of current local files.

`uplift split --holdout-only` seals the holdout before development split creation;
`make split` then freezes the five configured re-splits. The registry contains
counts, seeds, algorithm/library versions, rounding rules, and membership hashes.
Local sorted uint64 memberships are stored in ignored `artifacts/memberships/`.
Existing registries are verified and never silently replaced. `uplift split --verify`
checks local memberships without rewriting the registry. On a fresh workspace,
reacquire, validate, ingest, then run `uplift split --reconstruct`: it checks every
recomputed hash before restoring missing memberships and refuses to overwrite
corrupt ones. Reconstruction leaves the frozen registry unchanged.

Mechanical whole-file quality gates and label use for predeclared stratification
are the only pre-sealing operations. There are no holdout-specific outcome tables,
ATE estimates, exploratory balance/duplicate analyses, or policy evaluations in
this phase. Those analytical commands remain gated; future EDA uses development
records only. Seeds are not new experiments that permit repeated holdout selection.

Resource limits are declared in configuration: one DuckDB thread, 2 GB query
memory, a 6 GB spill ceiling, 65,536-row batches, and an 8 GiB free-disk preflight.
Splitting uses only row identifiers and two binary labels in memory, one split at
a time. The full cloud environment has an 8 GiB memory limit; raw and processed
artifacts remain local and their persistence across tasks is not guaranteed.

## Data source, attribution, and rights

Official dataset: [Criteo AI Lab](https://ailab.criteo.com/criteo-uplift-prediction-dataset/),
[criteo/criteo-uplift on Hugging Face](https://huggingface.co/datasets/criteo/criteo-uplift).
Use only the [pinned corrected v2.1 archive](https://huggingface.co/datasets/criteo/criteo-uplift/resolve/82811785048bb633de2d55c02bab4e57066e6423/criteo-research-uplift-v2.1.csv.gz).

Expected compressed size: 311,422,618 bytes; rows: 13,979,592; SHA-256:
`2716e1bf0fd157a93b5bf86924d9088419dfbac2022c6cd90030220634f616dc`.

Dataset attribution: Criteo AI Lab; Eustache Diemert, Artem Betlei, Christophe
Renaudin, and Massih-Reza Amini, *A Large Scale Benchmark for Uplift Modeling*,
AdKDD & TargetAd, 2018.

Repository code is MIT licensed (see LICENSE). The dataset is separately licensed
[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
No raw dataset is distributed here. Public derivative assets and commercial use
must respect the dataset license; the code license does not relicense the data.

Privacy subsampling and missing advertiser/experiment IDs limit causal
interpretation. A common treatment probability near 0.85 is an assumption;
there are no dates, customer IDs, measured costs, or revenue. Economics will be
explicitly hypothetical. The final headline holdout remains sealed until a
separately approved final evaluation with locked policies.
