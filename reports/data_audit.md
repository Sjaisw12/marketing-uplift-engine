# Development data audit — Phase 4

Analyzed **11,882,653 frozen development records only**. No source records were changed; no treatment effect, model, uplift estimate, or holdout outcome analysis was computed.

## Identity and access boundary

Source SHA-256: `2716e1bf0fd157a93b5bf86924d9088419dfbac2022c6cd90030220634f616dc`. Frozen registry SHA-256: `ab5350f8f17848680ef804311b3680c7dd3d8cf02bc2d5e8967d2dfda0d8937d`. Development membership SHA-256: `5257c0e7d472bff1a7e2589368f079f35093715ffd6449aaac0e574c3d397080`.

The verified development membership join was materialized before analytical aggregation. Every audit query uses that development table. Holdout IDs are read only for integrity and disjointness checks; no holdout label or feature summary is requested. All 19 protected source, membership, registry and Phase 3 provenance files had identical size and SHA-256 before and after the audit.

## Development sizes and frozen strata

| Treatment assignment | Development rows |
|---|---|
| Control (T=0) | 1,782,396 |
| Treated (T=1) | 10,100,257 |

Counts below describe the predeclared treatment × visit strata. They are not treatment-effect estimates; no arm visit-rate difference or inference is calculated.

| Partition | T0 V0 | T0 V1 | T1 V0 | T1 V1 |
|---|---|---|---|---|
| Development | 1,714,307 | 68,089 | 9,609,956 | 490,301 |
| 104729 train | 1,371,446 | 54,471 | 7,687,964 | 392,241 |
| 104729 validation | 342,861 | 13,618 | 1,921,992 | 98,060 |
| 130363 train | 1,371,446 | 54,471 | 7,687,964 | 392,241 |
| 130363 validation | 342,861 | 13,618 | 1,921,992 | 98,060 |
| 155921 train | 1,371,446 | 54,471 | 7,687,964 | 392,241 |
| 155921 validation | 342,861 | 13,618 | 1,921,992 | 98,060 |
| 181081 train | 1,371,446 | 54,471 | 7,687,964 | 392,241 |
| 181081 validation | 342,861 | 13,618 | 1,921,992 | 98,060 |
| 206369 train | 1,371,446 | 54,471 | 7,687,964 | 392,241 |
| 206369 validation | 342,861 | 13,618 | 1,921,992 | 98,060 |

## Feature summaries and distributions

All 12 f0–f11 features are anonymized pre-treatment numeric predictors; no business meanings are assigned. Standard deviation is sample-based. Percentiles are exact continuous quantiles computed one feature at a time.

| Feature | Mean | SD | Min | P01 | P25 | Median | P75 | P99 | Max |
|---|---|---|---|---|---|---|---|---|---|
| f0 | 19.6213 | 5.37728 | 12.6164 | 12.6164 | 12.6164 | 21.9242 | 24.4375 | 26.6728 | 26.7453 |
| f1 | 10.07 | 0.104772 | 10.0597 | 10.0597 | 10.0597 | 10.0597 | 10.0597 | 10.6795 | 16.3442 |
| f2 | 8.44655 | 0.299323 | 8.21438 | 8.21438 | 8.21438 | 8.21438 | 8.72325 | 9.04291 | 9.05196 |
| f3 | 4.17906 | 1.33638 | -8.39839 | -1.73323 | 4.67988 | 4.67988 | 4.67988 | 4.67988 | 4.67988 |
| f4 | 10.3388 | 0.343231 | 10.2805 | 10.2805 | 10.2805 | 10.2805 | 10.2805 | 11.9733 | 20.677 |
| f5 | 4.02852 | 0.430886 | -9.01189 | 2.23091 | 4.11545 | 4.11545 | 4.11545 | 4.11545 | 4.11545 |
| f6 | -4.15556 | 4.57781 | -31.4298 | -17.7773 | -6.69932 | -2.41111 | 0.294443 | 0.294443 | 0.294443 |
| f7 | 5.10174 | 1.20512 | 4.83381 | 4.83381 | 4.83381 | 4.83381 | 4.83381 | 11.4817 | 11.9984 |
| f8 | 3.93359 | 0.0566556 | 3.63511 | 3.7516 | 3.91079 | 3.97186 | 3.97186 | 3.97186 | 3.97186 |
| f9 | 16.0263 | 7.01696 | 13.1901 | 13.1901 | 13.1901 | 13.1901 | 13.1901 | 44.8936 | 75.295 |
| f10 | 5.33338 | 0.168162 | 5.30037 | 5.30037 | 5.30037 | 5.30037 | 5.30037 | 6.33696 | 6.47392 |
| f11 | -0.170966 | 0.0228227 | -1.32964 | -0.26735 | -0.168679 | -0.168679 | -0.168679 | -0.168679 | -0.168679 |

Additional P05/P10/P90/P95 values and arm-specific histogram counts are in `reports/data_audit.json`. Bins use unique pooled percentile cutoffs with right-closed intervals; ties collapse duplicate cutoffs. No rows are sampled.

## Missingness and numeric patterns

| Raw field | Missing | Nonfinite |
|---|---|---|
| f0 | 0 | 0 |
| f1 | 0 | 0 |
| f2 | 0 | 0 |
| f3 | 0 | 0 |
| f4 | 0 | 0 |
| f5 | 0 | 0 |
| f6 | 0 | 0 |
| f7 | 0 | 0 |
| f8 | 0 | 0 |
| f9 | 0 | 0 |
| f10 | 0 | 0 |
| f11 | 0 | 0 |
| treatment | 0 | 0 |
| visit | 0 | 0 |
| conversion | 0 | 0 |
| exposure | 0 | 0 |

| Feature | Distinct | Skewness | Zero % | Negative % | Integer-like % | Dominant value % | Tukey tail % | IQR |
|---|---|---|---|---|---|---|---|---|
| f0 | 2,121,030 | -0.246206 | 0 | 0 | 0 | 26.5 | 0 | 11.8212 |
| f1 | 60 | 13.9999 | 0 | 0 | 0 | 98.7693 | 1.23067 | 0 |
| f2 | 1,962,498 | 0.806552 | 0 | 0 | 0 | 52.2541 | 0 | 0.508863 |
| f3 | 535 | -3.18678 | 0 | 3.08166 | 0 | 81.8652 | 18.1348 | 0 |
| f4 | 248 | 8.88626 | 0 | 0 | 0 | 95.6603 | 4.33971 | 0 |
| f5 | 126 | -7.07537 | 0 | 0.161563 | 0 | 94.6956 | 5.30441 | 0 |
| f6 | 1,602 | -1.13589 | 0 | 73.5 | 0 | 26.5 | 1.27817 | 6.99376 |
| f7 | 542,599 | 4.52502 | 0 | 0 | 0 | 94.6956 | 5.30441 | 0 |
| f8 | 3,639 | -1.60572 | 0 | 0 | 0 | 52.2541 | 6.58382 | 0.0610661 |
| f9 | 1,551 | 2.82329 | 0 | 0 | 0 | 79.5057 | 20.4943 | 0 |
| f10 | 449,495 | 5.27831 | 0 | 0 | 0 | 95.6603 | 4.33971 | 0 |
| f11 | 126 | -14.8027 | 0 | 100 | 0 | 98.5523 | 1.44774 | 0 |

Skewness is DuckDB's bias-corrected sample Fisher–Pearson coefficient. Integer-like means absolute distance to the nearest integer ≤1e-9. Dominant value share uses exact value counts. Tukey tails fall strictly outside [Q1−1.5×IQR, Q3+1.5×IQR]; these are descriptive flags, not invalid records. Zero IQR, especially with discrete or concentrated values, can make a large tail fraction unsurprising. Negative values and repeated numeric levels have no known semantic interpretation.

Measured flags: |skewness| > 1: **f1, f3, f4, f5, f6, f7, f8, f9, f10, f11**; zero IQR: **f1, f3, f4, f5, f7, f9, f10, f11**; relative low variance: **none**. Low variance is defined as SD/max(1,|mean|) ≤1e-8 and is scale-dependent; exact constants are separately recorded. These flags do not select or remove features.

## Treatment/control covariate balance

| Feature | Control mean | Treated mean | SMD | Variance T/C | ECDF grid gap |
|---|---|---|---|---|---|
| f0 | 19.6544 | 19.6155 | -0.00722767 | 0.995459 | 0.00871683 |
| f1 | 10.068 | 10.0703 | 0.0237788 | 1.31178 | 0.00264573 |
| f2 | 8.4481 | 8.44628 | -0.00604788 | 0.989617 | 0.00346727 |
| f3 | 4.23291 | 4.16956 | -0.0488048 | 1.18616 | 0.0118235 |
| f4 | 10.3366 | 10.3392 | 0.00760013 | 1.02758 | 0.00242823 |
| f5 | 4.0393 | 4.02662 | -0.0304131 | 1.21755 | 0.00613757 |
| f6 | -4.00107 | -4.18282 | -0.0401932 | 1.07326 | 0.0128634 |
| f7 | 5.08001 | 5.10558 | 0.021531 | 1.08783 | 0.00613757 |
| f8 | 3.93466 | 3.9334 | -0.0225353 | 1.05202 | 0.00818561 |
| f9 | 15.8858 | 16.0511 | 0.0238599 | 1.07622 | 0.00653199 |
| f10 | 5.33189 | 5.33364 | 0.0105006 | 1.0511 | 0.00242823 |
| f11 | -0.170862 | -0.170985 | -0.00541927 | 1.03944 | 0.000960024 |

SMD=(mean_T−mean_C)/sqrt((sample variance_T+sample variance_C)/2). It describes feature imbalance, not an outcome effect. |SMD|≈0.1 is a conventional screening reference, not a randomization proof or an automatic pass/fail rule. For equal constants SMD is zero; unequal constants with a zero denominator are undefined. Variance ratio is undefined when control variance is zero.

ECDF grid gap is the largest absolute treatment/control cumulative-probability difference at pooled P01/P05/P10/P25/P50/P75/P90/P95/P99 cutoffs. Counts at these cutoffs are exact, but the grid maximum is a **lower bound on the full two-sample KS distance**, not an exact KS statistic or p-value. It checks distribution shape beyond a mean comparison, while variance ratios check dispersion. With millions of records, magnitude is more informative here than tiny significance p-values.

Largest measured absolute SMD: **f3: -0.0488048**. Largest measured ECDF grid gap: **0.0128634**. Small marginal gaps would not establish joint balance, known per-experiment propensities, or advertiser-wide validity.

## Repeated feature vectors

| Measure | Count |
|---|---|
| distinct vectors | 10,657,914 |
| rows | 11,882,653 |
| repeated vector groups | 926,589 |
| rows in repeated vectors | 2,151,328 |
| excess rows over distinct vectors | 1,224,739 |
| max multiplicity | 12 |

| Vector multiplicity | Number of distinct vector groups |
|---|---|
| 1 | 9,731,325 |
| 2 | 712,787 |
| 3-5 | 208,548 |
| 6-10 | 5,237 |
| 11-100 | 17 |
| >100 | 0 |

Rows participating in repeated vectors: **18.1048%**; excess rows over distinct vectors: **10.3069%**. Grouping uses exact equality of all 12 numeric features, without treatment, outcomes or exposure. Only aggregate multiplicities are exported. Identical vectors are not evidence of repeated users: there is no customer key. No observations were deduplicated. Such vectors may cross row-based development splits; cross-split vector overlap was not measured, and the frozen splits are not changed.

## Measured findings and interpretation

- All 12 feature summaries cover the full development pool. There are no missing/nonfinite values in the 16 retained raw fields. Observed negative values are valid anonymized numbers, not evidence of impossible records.
- The largest absolute marginal SMD is 0.0488048 (f3); the largest measured ECDF grid gap is 0.0128634 (f6). These describe marginal covariate differences without validating hidden experimental assignment mechanisms.
- Dispersion still differs: the largest treated/control variance ratio is 1.31178 (f1). A small mean gap should not be read as identical feature distributions.
- 8 nonconstant features have zero IQR. Features with at least 95% of observations at one numeric level: f1, f4, f10, f11. Dominant mass explains why a percentile summary or a Tukey flag can be misleading on its own; inspect the level counts and tails together.
- 18.1048% of development rows share their full feature vector with another row. This is a reason to qualify row-independence assumptions, not proof of duplicated users, and it does not authorize changing the frozen splits.
- All five seeded repetitions have the same stratum sizes because stratification uses the same parent counts and rounding. Matching stratum counts do not imply matching memberships; registry hashes establish membership identity.

## Implications and limitations

- Preserve all f0–f11 predictors and all observations for the later baseline phase. Do not invent feature semantics or infer monetary value from feature magnitudes.
- Compare any later scaling, clipping, transformations or feature pruning only inside the development training/validation protocol. Fit learned preprocessing on training rows only. This audit fits no transforms and changes no model recipe.
- Skew, concentrated mass, and Tukey tails motivate robust diagnostics and sensitivity checks; they do not justify deleting anonymous records. Low variance is scale-dependent and does not by itself establish uselessness.
- Arm sizes differ substantially by design. Later development-only effect and policy evaluation must quantify uncertainty and watch thin control-event strata. No effect or uncertainty interval is estimated in Phase 4.
- Exact repeated vectors are preserved; without real entity IDs, row-level splitting cannot establish entity independence or support customer-level interpretations.
- Privacy subsampling and missing advertiser/experiment IDs limit interpretation. Marginal covariate balance cannot identify the hidden assignment probabilities. No temporal generalization, revenue, measured costs, or production impact is inferred.
- The final holdout remains sealed for the single later approved evaluation. Development diagnostics must not be interpreted as holdout performance.

## Reproduction and resource limits

Run `make audit` with the existing verified Phase 3 artifacts. The command refuses missing/corrupt artifacts and does not reacquire, ingest, split or reconstruct data. The in-memory DuckDB development table may spill to the ignored cache: one thread, 2 GB query-memory limit and a 6 GB spill ceiling. Exact quantiles and distinct-value counts are evaluated one feature at a time; no full pandas dataframe is loaded. Only aggregate JSON and Markdown are published. Raw records, processed data and membership arrays remain outside Git.
