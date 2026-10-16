# Phase 4 — development-only data audit completion

Implementation and local verification are complete. Review/merge approval and
Phase 5 approval remain pending. The branch `codex/phase-4-data-audit` was created
from the specified merged main commit
`24b4e0b9d65cbf10761f8ec53e951d7965d9fd69` with a clean working tree. The finalized
nine-page roadmap was accessible; the audit follows its feature, data-discipline,
and sealed-holdout requirements.

## Existing artifacts preserved

A pre-switch SHA-256/size snapshot covered the archive, Parquet, frozen registry,
and all 12 local membership files. All 15 remained accessible and byte-identical
after switching branches and after the audit. The audit additionally protected the
acquisition manifest and three Phase 3 machine-readable evidence files: all 19
inputs were byte-identical before/after execution. No acquisition, ingestion,
reconstruction, partition replacement, or cleanup of ignored data was performed.

The frozen registry SHA-256 remains
`ab5350f8f17848680ef804311b3680c7dd3d8cf02bc2d5e8967d2dfda0d8937d`.
The archive and Parquet remain bound to the completed Phase 3 source-row mapping;
only hashes and development memberships were inspected for integrity.

## Measured findings

- Exactly **11,882,653 development records** were analyzed, containing **10,100,257
  treated** and **1,782,396 control** records. No holdout summaries were computed.
- Missing/nonfinite counts are **zero** for every retained raw field.
- The largest absolute feature SMD is **0.0488048 (f3)**; all are below 0.05.
  The largest measured percentile-grid ECDF gap is **0.0128634 (f6)**.
- Dispersion is not identical: f1's treated/control variance ratio is **1.31178**.
  These diagnostics do not prove joint balance, randomization, known per-experiment
  propensities, or advertiser-population validity.
- **Eight nonconstant features have zero IQR**. Strong skew and concentrated levels
  explain why Tukey fences cannot be interpreted as invalid-record detectors.
  No feature met the declared relative low-variance threshold; no feature was removed.
- Exact feature-vector grouping found **10,657,914 distinct vectors** and **926,589
  repeated-vector groups**. **2,151,328 rows (18.1048%)** participate in a repeated
  vector; there are **1,224,739 excess rows** above distinct vectors. Maximum
  multiplicity is **12**. All observations were retained.
- The full development treatment × visit strata and all five frozen train/validation
  stratum tables are recorded. No outcome contrast, ATE, uplift, or model was calculated.

`reports/data_audit.md` contains the complete twelve-feature summaries, quantiles,
patterns, balance diagnostics, multiplicities, interpretation, limitations and later
modeling implications. `reports/data_audit.json` records aggregate evidence,
method inputs and protected-file hashes. Neither file contains record-level vectors,
row IDs, predictions, or membership lists.

## Implementation and resources

`make audit` checks existing assets and materializes the verified development-only
membership join before any analytical aggregation. All feature, balance, duplicate,
and stratum queries use that table. Feature analysis accepts only f0-f11. Treatment
is the grouping key for covariate balance and counts; visit is used only for the
approved stratum counts. Conversion and exposure are checked for missingness and
finiteness only. No arm outcome-rate difference is calculated.

DuckDB uses the existing **one-thread, 2 GB query-memory, 6 GB spill** configuration
inside the cloud environment's 8 GiB memory ceiling. Exact quantiles and value
frequencies are computed one feature at a time; repeated vectors are grouped by
all twelve numeric features and exported as aggregate multiplicities only. No full
pandas dataframe or persistent processed-data copy is created. No transformations
or deduplication are applied.
Approximately 29 GiB disk space remains available.

## Checks actually run

- `make audit`: completed successfully on all existing development records.
- `make check`: **62 fast tests passed**; Ruff lint and formatting passed.
- Read-only full-data selection:
  `pytest tests/test_full_data.py tests/test_data_audit_full.py -m full_data -k 'not reconstruct' -q`:
  **5 passed, 1 deselected**. These recheck the original source identity and complete
  Parquet mapping, all audit input hashes, actual development strata, and aggregate
  coverage. The original reconstruction test was intentionally excluded because
  the assets are intact and its verification-report rewrite is unnecessary.
- New audit fixture tests use independent NumPy/SciPy/Counter references, verify
  exact strata and histogram totals, include synthetic heavy tails/constants,
  poison holdout-only features with a sentinel, refuse incomplete/corrupt/missing
  inputs, reject outcome columns for feature analysis, and abort publication if
  protected input hashes change.
- Final artifact snapshots, frozen membership verification, Git exclusions and
  diff checks passed. The frozen registry and Phase 3 code/configuration are unchanged.

Manual full-data CI now completes Phase 3 verification first, then runs the audit
and its read-only integration checks, uploading only small verification and audit
reports. No remote Phase 4 full-data workflow run is claimed here. Phase 3's
independent GitHub Actions verification was completed before this phase.

## Limitations and next gate

The ECDF grid maximum is a lower bound on the complete two-sample KS distance,
not an exact KS statistic/p-value. Low-variance flags depend on scale; Tukey fences
can flag ordinary minority levels when IQR is zero. Repeated vectors cannot identify
users, and cross-split vector overlap was not measured. No frozen membership is
changed in response to these diagnostics. Learned preprocessing must be fitted
only on development training subsets in a later approved phase.

The holdout seal is a tested workflow boundary, not OS isolation. Cloud storage
persistence is not guaranteed; existing assets should be retained, and any future
restoration must reproduce the frozen hashes. Phase 5 ATE and all modeling commands
remain unimplemented and gated. No merge or Phase 5 execution is authorized by this report.
