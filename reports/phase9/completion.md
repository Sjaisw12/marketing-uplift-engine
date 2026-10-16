# Phase 9 Stage A completion — preparation only

Only Stage A was authorized. Stage B remains unapproved and disabled. No final holdout rows were queried, scored, summarized or evaluated; no holdout treatment/visit statistics or performance metrics were calculated. No Phase 10/dashboard work.

## Review identities

- Final Stage A lock payload SHA-256: `fbd0ec32f8d97bbc1ffe03dd4a16a7937390d4ac570becef83b109cbc3d32b93`.
- Model-manifest payload SHA-256: `2e91bdae68cad12604c6aff3a9337b62e40df383f1ce6b2d3d4c1c58e08b8c9e`.
- Portable evaluation protocol SHA-256: `6cc04a9aa8d9c15ebff20402978921a4010af850e704e5cb8b20aed46189d1fc`.
Payload digests use UTF-8 canonical JSON: sorted keys, compact separators, nonfinite numbers forbidden. They hash the payload rather than its enclosing digest field or pretty-printed file bytes. Individual code/data/model hashes cover raw bytes.

Primary recommendation: model=null, ranking=null, reach=0, assignments=0 and hypothetical spending=0 for all eight unchanged Phase 8 economic scenarios. Incremental gain relative to no targeting is mathematically zero, not a statistically estimated zero advertising effect or proof of optimality. Absolute visits without advertising need not be zero. Development abstention reasons are retained; secondary diagnostics cannot replace the primary policy after holdout results.

## Source and preservation

Started a clean codex/phase-9-stage-a branch from merged main `aba2d1280b616d5eaafce885c5eddd32a2952527`. Training kernels, seed configuration, folds and estimators were committed before refits. Training used code commit6456a95, after a report-directory compatibility correction; no fit was attempted under a weakened historical protection check.
All 276 protected file/tree entries match before/after: archive/Parquet, twelve original memberships and registry, prior source/configurations/reports/models/predictions, complete historical MLflow trees and dependency lockfile. Stage A reports are isolated under reports/phase9 so frozen historical report globs remain valid. Existing artifacts were not recreated or deleted.
The nine-page roadmap remains authoritative/readable. Phase 8 approval is recorded; separate Stage A and Stage B checklists preserve independent approval gates.

## Actual development refits

All 11,882,653 frozen development records were used. Response fits 10,100,257 treatment records/490,301 visits; control fits 1,782,396 records/68,089 visits. S fits all development records. No validation performance was used for tuning, weighting, calibration or early stopping.
All models have 200 trees and the unchanged frozen LightGBM hyperparameters. User predictors are exactly f0–f11; S has one additional separately supplied intervention indicator. Treatment routes arm fits; exposure/outcomes/identifiers are not user predictors.
Nuisance folds have 3,960,885 /3,960,884 /3,960,884 records. Six fits exclude their corresponding inner fold and use only the appropriate arm. Minimum nuisance training event support: 45,239 control visits and 326,588 treatment visits. Shared three-model arm averages evaluate all policies fairly; the new final S is the predeclared nuisance sensitivity.

| Model | Development fit rows | Trees | Model file SHA-256 |
|---|---:|---:|---|
| response | 10,100,257 | 200 | `f4118881216373b6ebdcb4ee52ac538bbe21853d9227d8a437d64649fdaf54ef` |
| control | 1,782,396 | 200 | `188dee9a3d1f7fbb90838060057b7ffd9b663ffc7515dc7030a801efa4e02fa1` |
| s_learner | 11,882,653 | 200 | `6e6abe2b64d4440416fa4c3164164f06a1707a68c9fa59dd6e7c6b47bff8e1f7` |
| nuisance-0-0 | 1,188,415 | 200 | `5c855c98308899ba74edebf37cfb30a349cadd221c719ef4c87bf860d61bd765` |
| nuisance-0-1 | 6,733,353 | 200 | `a69101d4a6b29d4882da2c8f5a0af1619fd34a939317c6c27205af8101cc584a` |
| nuisance-1-0 | 1,187,868 | 200 | `392d31211fad1077500c332f5a7bdc7e425f17f9bc54fbfaf11c6cff7b653dbe` |
| nuisance-1-1 | 6,733,901 | 200 | `cbe59d2a5b6abc986494420094bc18791498dc63958f5052b441d8e097223cea` |
| nuisance-2-0 | 1,188,509 | 200 | `b9b95c8b321a608523a5ca9896b82b646c9af09204701f18f8fd511d2f6afcf5` |
| nuisance-2-1 | 6,733,260 | 200 | `6092033be93f9504319cabd22ca09fa5796592e97424c0deeebb0837dec5c5b2` |

All exact fit-ID/mask hashes, fold labels, canonical feature order, seeds, versions and recipe are in model_manifest.json and nuisance_manifest.json. Raw development caches, fold labels, model files, probes and MLflow remain ignored.

## Evaluation methodology prepared, not executed on holdout

Frozen diagnostic policies: random/response/S/T at 10/20/30/40/50%, none and all anchors. Ranking/ties, ceil reach, strict floor reach caps, Decimal budgets and eight hypothetical economics remain fixed. No-targeting matched-spending comparisons also target nobody; positive reaches have separate actual spending.
IPW/shared DR/final-S DR are implemented under assumed e=.80,.825,.85,.875,.90, with .85 reference only. No observed holdout assignment fraction substitutes for those assumptions. The evaluator returns 375 continuous contribution coordinates. Its 765 simultaneous contrasts comprise 20 gains +30 same-reach model contrasts +1 all gain, crossed with 15 evaluator/propensity scenarios.
Two thousand shared Gaussian-multiplier draws preserve pairing. Pointwise intervals and two-sided max-standardized simultaneous intervals are separate. The primary IID covariance is sample covariance/N. Mandatory secondary stratified sensitivity uses fixed observed T×visit composition and sum(w_h^2*S_h/n_h), with frozen original cohort rankings. It does not replace IID uncertainty. Empty strata have weight0; a nonempty stratum below two rows makes that sensitivity undefined. Conditioning can give zero aggregate contrast variance; it is not causal certainty.

## Actual verification

- make check: **165 fast tests passed**, 18 full-data tests deselected; lint and formatting pass.
- Eight historical Phase 6–8 read-only integration checks passed in the nine-test development verification batch (144.91s). The final Stage A lock was separately reverified after review-binding checks: **1 passed in 9.94s**. Nine unique permitted full-data tests are covered; all outcome queries joined only development IDs.
- Final 2,048-row DEVELOPMENT correctness probe: maximum independent row mean error 5.2042e-17, covariance error 1.7212e-18, stratified covariance error 2.0329e-19. All 375 coordinates and 765 contrasts were checked. This is not out-of-sample performance.
- Independent 511-row synthetic reference across three batch sizes: mean discrepancy<=2.4425e-15, covariance<=1.4225e-16, stratified covariance<=1.3878e-17. Known-answer policy gains, paired max-t bands, singular/zero variance and undefined small strata pass.
- Nine real model reloads produce bit-identical development probe probabilities. Full fit masks/IDs, nuisance exclusion and held-fold probe predictions agree with saved evidence. New MLflow model copies and manifest match their exact hashes.
- All three real holdout APIs reject flags, claimed approval payloads and environment variables before I/O. Mixed/holdout IDs fail the Stage A development query boundary. Disabled workflow has an unconditional false job gate.
- Checkout-relocation test preserves public protocol identity; manifest-substitution/preservation-fingerprint tampering fails. Public-lock verification opens no datasets/models.
- Resume is byte-identical and performs no refit. Every original model hash and primary recommendation survived portable review sealing unchanged. See verification.json, synthetic_reference.json and reproducibility.json.

## Portable review and lineage

Historical protocol identities contain absolute workspace paths. The new review identity uses repository-relative file keys, complete code/configuration/test hashes and fixed historical evidence. This lets public CI validate the review lock from another checkout without loading data/models or changing historical protocols.
Original preparation records, models and MLflow provenance are retained. Review seals bind exact unchanged training/evaluation kernels, seeds, caches and model bytes. Training and evaluation identities are recorded separately; no models were retrained to correct metadata portability. The current lock above is the review candidate; older preparation identities are not Stage B approval.

## Resources and persistence

Initial preparation elapsed 443.62s; summed worker fit/verification time 392.29s. Review sealing and subsequent verification/reporting are additional overhead. Maximum worker ru_maxrss 3.266GiB; parent high-water 3.164GiB. Worker high-water can include process start-up/pre-exec history; it is not a per-estimator allocation.
Existing 8GiB/two-CPU settings retained. Fits ran sequentially in separate processes; DuckDB 2GB/one thread and batch 65536, with memory-mapped development caches. Environment-wide memory peak 8GiB includes file cache. Cap/reclamation events rose 18→516; OOM/kill counters remained0. No smaller sample, substitute estimator or altered recipe was used.
Free disk at preparation completion: 24.131GiB. New private Stage A cache/models/probes/manifests occupy approximately 1.2GiB. Separate local MLflow preparation/review runs record exact provenance and models; earlier phases remain read-only.
Cloud-local persistence across new tasks is not guaranteed. Git contains code and aggregate evidence, not model weights or data. Deliberately restore missing verified private artifacts; do not automatically reacquire, reconstruct splits or rerun whole-source outcome validation as Stage A prerequisites.

## Stage B blocker and recovery contract

**Stage B is NOT authorized and remains disabled.** No verified required-reviewer approval integration or independently durable atomic create-once execution-receipt backend is configured in this implementation. A boolean workflow input, local JSON or an environment name alone cannot enforce those requirements. No real execution-start receipt was written during Stage A.
Future activation requires separately reviewed gate/backend integration, a new matching code lock, and explicit approval bound to exact lock AND model-manifest digests. A durable execution-start receipt must be consumed before outcome access; interruptions cannot reset it for another model/policy. Recovery is restricted to the same locked execution and verified checkpoints. Local logical API guards are not OS-level isolation; real holdout readers therefore remain disabled.
Stage A PR approval/merge is not Stage B approval. No final holdout statistics, performance, policy re-selection, dashboard or Phase 10.

## Statistical limitations

Unknown experiment propensities, non-uniform privacy selection, missing customer/experiment identifiers, possible dependence, original outcome stratification and development selection remain unresolved. DR requires identification plus appropriate nuisance correctness; it does not validate those assumptions. Both uncertainty methods condition on fitted models/fixed policies and omit refit/selection/dependence uncertainty. The five development splits overlap; no independent-replication CI is used. Hypothetical economics establish no real revenue, ROI, cost savings or causal superiority.

## Files and CI

Added configs/phase9.toml; docs/PHASE9_STAGE_A_PROTOCOL.md; final_access.py, final_fit_worker.py, final_metrics.py, final_stage_a.py, final_verification.py; final statistical/model/access/portability/full-data tests; Stage A and disabled Stage B workflows; aggregate reports/phase9 evidence. Updated CLI, Makefile, README, INTERVIEW, phase checklist and cheap CI public-lock verification.
PR CI runs Python 3.11/3.12 synthetic checks plus public-lock verification without private artifacts. The manual Stage A public workflow does not acquire, ingest, reconstruct or open outcomes. Local private development verification is not claimed as independent remote refit verification.

Wait for Stage A review. Do not merge without approval; Stage B needs separate explicit approval and its missing enforcement integrations.
