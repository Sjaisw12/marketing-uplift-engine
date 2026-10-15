# Marketing Uplift & Causal Decision Engine

An offline decision analysis of **incremental visits** under randomized advertising
assignment in the corrected Criteo Uplift v2.1 release. Estimates describe the
released benchmark population, with uncertainty; they do not measure realized
revenue, advertiser-wide lift, or production impact.

## Current state

Phase 2 acquisition is implemented. `make acquire` verifies the official compressed
archive before writing `data/manifest.json`; a successful receipt distinguishes
byte verification from pending row-count/schema validation. No partition, model,
or effect has been created. Later-stage commands deliberately return a nonzero
exit status until their implementation phase is approved.

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
| `make status` | Display protocol and honest scaffold status | 1, available |
| `make acquire` | Download pinned gzip, verify bytes and SHA-256, write provenance | 2, available |
| `make validate` | Data contract validation | 3 |
| `uv run --locked uplift validate --full` | Expensive full-file contract stage | 3 |
| `make ingest` | Audited typed Parquet | 3 |
| `make split` | Seal final holdout once and freeze five development re-splits | 3 |
| `make audit` | Development EDA | 4 |
| `make ate` | Development ATE with 95% CI | 5 |
| `make baselines` | Random, visit propensity, S-learner; MLflow logs | 6 |
| `make reproduce` | Sequential rerun entry point, available after implementation | 2–6 |

`make reproduce` currently acquires/verifies the archive and then stops at the
unimplemented contract-validation gate. It will never authorize a final holdout evaluation. Reruns must reuse frozen split files.
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
104729, 130363, 155921, 181081, and 206369. These are **declarations only**;
Phase 3 must record actual membership hashes and seeds in `artifacts/splits.json`.
Never report a configuration file as evidence of frozen data partitions.

Features are exclusively `f0`–`f11`. Exposure is post-assignment. Treatment, visit,
and conversion are excluded from exported `X`. The S-learner receives treatment
separately as its intervention indicator, as required by the authoritative roadmap.
The primary outcome is visit; conversion is reserved for V2.

The full-data CI job is disabled until acquisition and contract validation exist.
After Phase 3, enable the repository variable `FULL_DATA_VALIDATION_ENABLED=true`
and dispatch the workflow. It caches archive bytes by expected digest and reruns
verification; cheap checks run on every PR without downloading data.

## Acquisition and verification

```sh
make acquire
```

This uses `huggingface_hub.hf_hub_download` with the immutable revision and official
endpoint, no API token, and a temporary staging directory inside `data/raw/`.
It verifies basename, exact compressed byte count and SHA-256 before atomic
promotion. The final archive is read-only. Cached archives are reverified on every
invocation; mismatches stop the command without replacing the archive or receipt.
No observations are decompressed or analyzed during acquisition.

`data/manifest.json` records source URL, revision, digest, bytes, license, citation,
UTC acquisition/verification timestamps and expected row count. Actual `row_count`
is null and `schema_validated` is false until Phase 3. For an existing local archive
without a receipt, acquisition time is unknown rather than inferred. A receipt is
historical evidence; downstream ingestion must independently reverify the bytes.

Restricted environments must allow `huggingface.co` and storage hosts reached by
its redirects. A blocked download fails without publishing an archive or receipt.
Do not substitute an unofficial mirror to bypass the source lock or network policy.

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
