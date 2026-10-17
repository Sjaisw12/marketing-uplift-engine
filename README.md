# Marketing Uplift & Causal Decision Engine

An offline decision analysis of **incremental visits** under randomized advertising
assignment in the corrected Criteo Uplift v2.1 release. Estimates describe the
released benchmark population, with uncertainty; they do not measure realized
revenue, advertiser-wide lift, or production impact.

## Current state

Phase 9 **Stage A only** prepares a final policy/evaluation lock. Phase 8 was
independently verified through GitHub Actions and merged. Stage B is neither
approved nor enabled; no final holdout rows, statistics or predictions are used.

The primary recommendation preserves Phase 8's unanimous abstention: zero
assignments and hypothetical spending. Its zero gain relative to no targeting is
a mathematical identity, not evidence that advertising is ineffective or that
abstention is optimal. Absolute visits without targeting need not be zero.

Stage A adds nine predetermined full-development diagnostic refits while preserving
all historical models/results. Random, response, S and T at 10–50% reach and none/all
anchors are frozen secondary diagnostics, never substitutes chosen after holdout
results. Prices remain hypothetical; no causal superiority or financial profit is
established by constant-propensity scenarios or narrow working-model intervals.

See [Stage A protocol](docs/PHASE9_STAGE_A_PROTOCOL.md),
[Stage A completion](reports/phase9/completion.md),
[public lock and model evidence](reports/phase9/stage_a.json), and
[development-only verification](reports/phase9/verification.json).
Earlier [Phase 8 decisions](reports/phase_8_decisions.md),
[Phase 7 comparisons](reports/phase_7_comparison.md), and
[Phase 6 results](reports/phase_6_baselines.md) remain immutable.

The final holdout remains sealed. Stage A approval/merge does not authorize Stage B.
No Streamlit or Phase 10 work is implemented.

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
| `make audit` | Development EDA | 4, available |
| `make ate` | Descriptive development assignment contrast and nominal 95% CI | 5, available |
| `make final-prepare` | Stage A development-only final refits/lock; Stage B disabled | 9A, available |
| `make decisions` | Hypothetical development budget/abstention simulator | 8, available |
| `make advanced` | T-learner, shared cross-fit DR and paired multiplier evaluation | 7, available |
| `make baselines` | Random, visit propensity, S-learner; MLflow logs | 6, available |
| `make reproduce` | Sequential rerun entry point, available after implementation | 2–6 |

`make baselines` executes all five fixed recipes and resumes completed splits only
when protocol, provenance and private artifact hashes match. First execute
`uv run --locked uplift baselines --first-split`, then run the read-only Phase 6
full-data tests with `PHASE6_EVIDENCE=reports/phase_6_first_split.json` before continuing. `make reproduce` includes the already approved
stages through Phase 6; it never authorizes a final holdout evaluation. Use
`make baselines` directly in an intact workspace to preserve prior acquisition and
report timestamps. Reruns reuse frozen memberships.
Work proceeds by completed checklist and explicit phase approval, without calendar
scheduling or effort estimates. See [phase checklists](docs/PHASES.md).

## Layout and declared protocol

- `src/marketing_uplift/`: package and command interface.
- `configs/project.toml`: source identity, schema, experiment protocol and local tracking.
- `tests/`: fast checks; read-only full-data tests use the `full_data` marker.
- `data/raw/`, `data/processed/`: ignored data; `data/manifest.json` will record acquisition.
- `reports/`: human-readable audit and results; no row-level exports.
- `artifacts/`: committed split registry and ignored local row-level/model artifacts.
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
The workflow then runs the development audit and contrast, each followed by
read-only full-data checks. An optional manual `run_baselines` input enables the
first-split gate, all five baseline evaluations and read-only Phase 6 verification.
It uploads only aggregate reports, never models, predictions, MLflow records or data.
Only small verification and audit reports are uploaded. Cheap fixture checks run on every
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
Phase 3. The later development audit and descriptive contrast obey this boundary;
Phase 6 modeling uses only frozen development train/validation rows. Seeds are not new experiments that permit repeated holdout selection.

Resource limits are declared in configuration: one DuckDB thread, 2 GB query
memory, a 6 GB spill ceiling, 65,536-row batches, and an 8 GiB free-disk preflight.
Splitting uses only row identifiers and two binary labels in memory, one split at
a time. The full cloud environment has an 8 GiB memory limit; raw and processed
artifacts remain local and their persistence across tasks is not guaranteed.

## Phase 4: development-only descriptive audit

Run `make audit` using the existing Phase 3 assets; it does not acquire, ingest,
reconstruct, or change frozen splits. It verifies the artifacts, materializes only
the development membership join, and computes bounded DuckDB aggregates. All
protected data and Phase 3 provenance files are hashed before and after execution.
The command publishes aggregate JSON and a readable Markdown report only.

The report includes all 12 feature distributions, exact percentiles, missingness,
skewness, Tukey tails, distinct values, dominant mass, zero/negative/integer-like
patterns, relative low-variance flags, treatment/control covariate SMDs and variance
ratios, percentile-grid ECDF comparisons, repeated-vector multiplicities, and
frozen development treatment × visit stratum counts. No record is removed,
deduplicated, imputed, clipped, transformed, or used to fit a model.

Measured highlights: zero missing/nonfinite values; largest |SMD| about 0.0488
(f3), while f1 has a treated/control variance ratio about 1.312; eight nonconstant
features have zero IQR; 2,151,328 development rows (18.10%) share a complete feature
vector with another row. These are descriptive results, not evidence of advertiser
population balance or repeated customer IDs. Pooled percentile-grid ECDF gaps are
lower bounds on full KS distances; Tukey flags on concentrated/discrete features
are not invalid-record diagnoses. Consult `reports/data_audit.md` for definitions,
actual counts, interpretation, and modeling implications.

`make check` includes synthetic statistical-reference, holdout-sentinel, artifact
preservation, leakage-boundary, and failure tests. After `make audit`, run the
read-only full-data audit integration checks with:

```sh
UV_CACHE_DIR=.cache/uv uv run --locked pytest tests/test_data_audit_full.py -m full_data
```

The original Phase 3 reconstruction integration test rewrites its verification
report; it is not needed for an audit of intact assets. Phase 4 full-data checks
verify existing memberships and metadata without reconstructing them. In a fresh
CI workspace, the workflow first completes Phase 3 verification, then generates
the audit and checks that its protected inputs stayed unchanged.

## Phase 5: descriptive assignment contrast and nominal uncertainty

Run `make ate` with the existing verified Phase 3/4 artifacts. It projects only
row IDs, treatment assignment and visit through the development-only boundary,
reconciles exact counts with Phase 4, and hashes all 22 protected input files
before/after execution. It does not acquire, ingest, reconstruct, regenerate splits,
or overwrite prior reports. The five overlapping repetitions are not pooled.

The analysis reports n and observed visits for each arm, p_T and p_C, and p_T−p_C.
Percentage points are 100 times the absolute probability difference; per-1,000
values are 1,000 times that difference. Neither is a relative percentage change.
The predeclared interval combines two uncorrected Wilson score intervals using
Newcombe's hybrid score formula (method 10). All formulas, the binary64 numerical
method, interval endpoints and interpretation are in `reports/development_ate.md`.

The interval is **nominal working-model uncertainty**, not exact randomization
inference or a correction for outcome-stratified development selection. Independent
Bernoulli rows/arms are unverified assumptions; missing entity and experiment IDs
prevent justified cluster correction. Non-uniform subsampling and unknown pooled
assignment propensities can bias the contrast. Causal ITT interpretation requires
additional exchangeability, consistency, no-interference and selection assumptions.
There is no exposure conditioning, treatment-on-the-treated effect, or claim about
ROI, revenue, advertiser-wide effects, or production impact.

Fourteen frozen reference cases, including unequal sizes and zero/all events,
agree with Statsmodels 0.14.5 and independent 70-digit Decimal score-quadratic
calculations to absolute tolerance 1e-12. CI uses the committed offline fixture;
Statsmodels is not a runtime or test dependency. To independently regenerate it
in an isolated temporary reference directory with network access enabled:

```sh
UV_CACHE_DIR=.cache/uv uv pip install --python .venv/bin/python \
  --target /tmp/ate-reference-packages --no-deps statsmodels==0.14.5 patsy==1.0.2
.venv/bin/python scripts/generate_newcombe_references.py \
  --reference-path /tmp/ate-reference-packages --output /tmp/newcombe-reference.json
```

After `make ate`, the read-only integration check is:

```sh
UV_CACHE_DIR=.cache/uv uv run --locked pytest tests/test_development_ate_full.py -m full_data
```

The manual GitHub Actions workflow generates the contrast after Phase 3/4
verification, tests its counts/interval/preservation, and uploads small reports only.
Run `make check` for the offline statistical and synthetic integration tests.
No remote Phase 5 full-data workflow result is claimed by the local completion report.

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


## Phase 7 execution and verification

Use `make advanced` directly in this intact workspace. It verifies existing Phase 6
source/model/prediction/protocol hashes, reuses the treated-response models, and
writes only new Phase 7 artifacts and a separate local MLflow experiment. It never
runs acquisition, ingestion, outer split reconstruction or Phase 6 training.
Do not use `make reproduce` to preserve existing report/acquisition timestamps:
that older entry point reruns prior stages through Phase 6.

The real first-split gate, followed by the unchanged other four recipes, is:

```sh
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 uv run --locked uplift advanced --first-split
PHASE7_EVIDENCE=reports/phase_7_first_split.json OPENBLAS_NUM_THREADS=2 \
  uv run --locked pytest tests/test_advanced_full.py -m full_data
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 make advanced
OPENBLAS_NUM_THREADS=2 uv run --locked pytest tests/test_advanced_full.py \
  tests/test_baselines_full.py -m full_data
```

Nuisance fold labels are auxiliary training-only files; they do not alter any of
the twelve frozen memberships. Their hashes are published before first training.
No new dependencies are needed and `uv.lock` remains unchanged. Existing matching
Phase 7 completed runs resume only after artifact/provenance checks.

An optional manual GitHub Actions `run_advanced=true` dispatch recreates prerequisites
in its fresh workspace, verifies Phase 6, then gates Phase 7 first-split/all-five
execution and preservation checks. Only aggregate evidence is uploaded. Raw data,
models, row-level predictions, OOF records and MLflow remain local and Git-ignored.
These cloud-local artifacts are not guaranteed to persist into another task; do
not recreate files that are already present and valid.

## Phase 8 execution and verification

Use existing verified artifacts directly; do not rerun acquisition, ingestion or
model training in this intact workspace:

```sh
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 uv run --locked uplift decisions --first-split
OPENBLAS_NUM_THREADS=2 uv run --locked uplift decisions --verify-first-split
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 make decisions
OPENBLAS_NUM_THREADS=2 uv run --locked pytest tests/test_decisions_full.py -m full_data
```

The first-split receipt gates the remaining four. All five outcome-blind role-label
hashes are frozen before Phase 8 outcomes are queried. Selection recommendations
and assessment assignment hashes are persisted before assessment outcome access.
Changing assessment outcomes cannot change recommendations. These auxiliary roles
do not replace or modify any original frozen memberships.

`configs/phase8.toml` fixes eight entirely hypothetical economic scenarios. Budget
scales as budget-per-eligible-record times role size, with unchanged cost/value.
Positive policies use top ceil(q*N), while the strict actual reach cap uses
floor(maximum_reach*N); an infeasible boundary candidate is rejected, not silently
trimmed. Budget below the smallest positive 10% grid reach produces a distinct
no-feasible-reach result. Free assignments retain the evidence and reach gates.

All five propensity assumptions and IPW/primary-DR/saved-S-DR specifications enter
the conservative stress objective. Two thousand correlated Gaussian draws provide
one-sided simultaneous lower bounds over 300 marginal coordinates within each role
and split. These bands do not protect against causal misspecification. Pointwise
assessment intervals and equal-spending comparisons are explicitly separate.

`reports/phase_8_metrics.json` records provenance, roles, marginal evidence,
recommendations and paired comparisons; `phase_8_economics.json` transforms every
feasible fixed policy into hypothetical spending/net-value scenarios. Markdown
reports explain limitations and stability. No row-level outputs enter Git.
Local artifacts live under ignored `artifacts/phase8/<protocol>/<seed>/`; new local
MLflow experiments retain private evidence and aggregate reports. Matching resumes
verify hashes and do not refit models or overwrite prior results.

Manual GitHub Actions `run_decisions=true` runs prerequisite phases in its own
fresh workspace, then gates the first Phase 8 split before all-five verification.
That workflow restoration does not authorize recreating artifacts in this intact
workspace. Only aggregate reports are uploaded. Local checks are not a claim of
independent remote full-data verification.

## Phase 9 Stage A — safe preparation and review

In this intact workspace, use only the Stage A command and read-only verification:

```sh
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 make final-prepare
OPENBLAS_NUM_THREADS=2 uv run --locked uplift final-prepare --verify
uv run --locked uplift final-prepare --verify-public-lock
OPENBLAS_NUM_THREADS=2 uv run --locked pytest tests/test_final_stage_a_full.py -m full_data
```

The public-lock check opens no datasets/models and runs on fresh CI checkout.
Private verification reads only development correctness probes and verified files.
Do not run older acquisition/full-validation/reconstruction/reproduce workflows as
Stage A prerequisites: they scan whole-source outcome columns. No such workflow is
needed in this intact workspace. Missing private artifacts require deliberate,
verified restoration, never automatic reconstruction or a weaker fallback.

New full-development refits use the unchanged Phase 6 hyperparameters and fixed
Phase 9 seeds. Three arm/S models plus six development-only nuisance regressions
are stored under ignored `artifacts/phase9/<protocol>/`, with exact fit-ID/mask and
fold hashes. Separate local MLflow records provenance/models. Development probes
verify arithmetic, exclusion and reloads; they are not new out-of-sample validation.
All earlier models, reports, memberships, MLflow trees and uv.lock remain unchanged.

The final diagnostic evaluator implements IPW, shared DR and final-S DR under five
assumed propensities; 2,000 correlated Gaussian draws; 765 two-sided simultaneous
contrasts; and distinct pointwise intervals. A mandatory secondary T×visit-stratified
covariance sensitivity fixes stratum composition and can yield zero conditional
variance for some contrasts. Neither interval method is exact randomization inference
or a remedy for hidden propensities, privacy selection, dependence or model error.
No method is selected by favorable results. The pure evaluator runs only on synthetic
and permitted development arrays during Stage A.

**Stage B is disabled in code and workflow**, regardless of flags or local approval
files. No verified protected reviewer approval backend or independently durable
create-once execution-receipt store is integrated. A GitHub environment name or
ignored local JSON would not enforce these requirements. Future activation needs
reviewed gate integration, a new code lock and separate approval tied to exact lock
AND model-manifest digests. No real execution-start receipt is created during Stage A.

If later authorized, policy/model/scoring hashes must persist before the first
outcome read, and a durable execution receipt must already exist. A failed execution
cannot reset that receipt to try another model/policy. Recovery is limited to the
same reviewed lock and verified checkpoints. Logical API guards are not OS-level
access isolation; the real holdout interfaces therefore remain unimplemented and
deny access. The final holdout is not consumed by these preparation tests.

Stage A reports live under `reports/phase9/` so historical Phase 8 report fingerprints
remain unchanged. Private data/models are not committed; cloud-local persistence
is not guaranteed. The Stage A PR is for review only, not permission for unsealing.

Stage A lock and model-manifest identifiers are canonical JSON payload SHA-256,
not hashes of pretty-printed wrapper bytes. Original training and portable review
identities are both preserved; artifact/lock roots are recorded in stage_a.json.
The portability correction reuses every original model byte without refitting.


### Stage B safeguard preparation (disabled)

The separately approved preparation adds owner-signed Ed25519 authorization,
a fixed-cohort Git receipt adapter, private checkpoint hashes, and synthetic
execution/recovery state tests. Stage A models, policy and lock remain unchanged.
No holdout data is accessed and no production receipt exists.

See [manual setup and limitations](docs/STAGE_B_SAFEGUARDS.md). Mock/local Git tests
do not establish GitHub ruleset enforcement or independent backup durability.
Live write tests and final execution each require separate approval.

```bash
uv run --locked pytest tests/safeguards -q
uv run --locked python -m execution_safeguards verify-lock
```

The metadata verifier does not open private data or model weights. Real scoring and
outcome interfaces always deny access; the production public key is unconfigured.


### Stage B coordinator preparation

The [synthetic-only coordinator](docs/STAGE_B_COORDINATOR.md) now connects signed
authorization, a fixed-cohort receipt, append-only stage events, sealed predictions,
private backup/restore and separately signed recovery. The [completed live synthetic
receipt evidence](docs/STAGE_B_SYNTHETIC_INTEGRATION.md) is preserved; never repeat it.
Real holdout access remains disabled and the production public key remains unset.
The current lock is `reports/phase9/coordinator/implementation_lock.json`; the
previous Stage A and safeguards locks remain immutable historical evidence.

## Disabled production adapter preparation

The owner public key is pinned in an additive configuration. Real Stage B entry
points remain disabled. See [adapter operations](docs/PRODUCTION_ADAPTER.md) for
strict Parquet projections, model/seal verification, bounded private export and
unresolved full-size private-transfer requirements. No final holdout scoring or
evaluation has been run. Historical execution locks remain unchanged.
