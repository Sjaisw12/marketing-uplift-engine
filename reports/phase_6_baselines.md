# Phase 6 — development machine-learning baselines

All results below are measured on the five frozen development validation sets.
Each contains 2,376,531 rows; overlapping splits are stability checks, not independent experiments.
The sealed 2,096,939-row final holdout was excluded. All 25 protected input files remained identical.

## Interpretation and frozen methods

These are assumption-dependent IPW scenario functionals, not proven causal improvements.
The causal target would be V_causal(pi)=E[Y(pi(X))] in the released population, with gain
E[pi(X)*(Y(1)-Y(0))] over assigning nobody. The observable scenario functional is
Phi_e(pi)=E[pi*T*Y/e+(1-pi)*(1-T)*Y/(1-e)]; tables estimate this by sample means.
Differences of Phi_e are identifiable released-sample functionals for each fixed e; their
interpretation as differences of causal policy values requires the assumptions below.
The reference constant e=0.85 is not a verified individual assignment probability.
Non-uniform privacy subsampling, pooled experiments and unknown assignment probabilities can bias
all constant-propensity scenarios. Sensitivity does not establish identification.
Causal policy values require consistency, no interference, positivity, exchangeability and correct
assignment probabilities in the released population. No exposure conditioning or ROI inference is used.

Treated-response LightGBM predicts who visits under assignment; it can prioritize people who would
visit anyway. The S-learner ranks m(X,1)-m(X,0), a model contrast rather than an observed individual effect.
Both use f0–f11 only as user predictors. The S-learner intervention is supplied separately.
Histogram boosting handles nonlinear patterns in the anonymized numeric features without scaling.
The fixed 63-bin, 31-leaf, minimum-1,000-record recipe limits memory and leaf complexity; 200 rounds
avoid validation-driven early stopping. Unweighted binary loss preserves probability-scale targets.
A linear probability/logistic baseline would be cheaper but less flexible; additional estimators
and tuning require later approval. Calibration and individual-effect accuracy are not established
by high visit-prediction AUC. S-learner regularization can suppress treatment interactions.
The complete pre-performance recipes, ranking rules, formulas and integration convention are in
[PHASE6_PROTOCOL.md](../docs/PHASE6_PROTOCOL.md). No hyperparameter or reach selection occurred.

Areas use all n+1 prefixes and trapezoidal integration, not the five reporting reaches.
IPW Qini is unnormalized area above the random diagonal. Negative estimates remain negative.
Values and gains below are per 1,000 eligible validation rows, not per selected user.

## Reference scenario: five-split descriptive means and ranges

| Reach | Ranking | Value mean [min, max] /1,000 | Gain over none mean /1,000 |
|---|---|---:|---:|
| 10% | random | 39.2816 [39.2165, 39.3959] | 1.0803 |
| 10% | response | 46.3119 [46.2536, 46.3888] | 8.1106 |
| 10% | s_learner | 47.5606 [47.3191, 47.8590] | 9.3593 |
| 20% | random | 40.2951 [40.0912, 40.3671] | 2.0938 |
| 20% | response | 47.8638 [47.7008, 47.9518] | 9.6625 |
| 20% | s_learner | 48.2557 [48.0826, 48.3597] | 10.0543 |
| 30% | random | 41.3570 [41.2422, 41.4940] | 3.1557 |
| 30% | response | 48.1863 [48.0885, 48.2630] | 9.9850 |
| 30% | s_learner | 48.3292 [48.2514, 48.4390] | 10.1279 |
| 40% | random | 42.3460 [42.0872, 42.5059] | 4.1446 |
| 40% | response | 48.3487 [48.2894, 48.4064] | 10.1473 |
| 40% | s_learner | 48.4012 [48.2631, 48.5232] | 10.1999 |
| 50% | random | 43.4136 [43.2220, 43.6195] | 5.2123 |
| 50% | response | 48.4018 [48.3673, 48.4390] | 10.2005 |
| 50% | s_learner | 48.4617 [48.3974, 48.5364] | 10.2604 |

## Per-split support, anchors and diagnostics

| Seed | Treated / control validation | None / all value per 1,000 | Response AUC / AP | S factual AUC / AP |
|---|---:|---:|---:|---:|
| 104729 | 2020052 / 356479 | 38.2013 / 48.5433 | 0.9463 / 0.5225 | 0.9465 / 0.5174 |
| 130363 | 2020052 / 356479 | 38.2013 / 48.5433 | 0.9465 / 0.5265 | 0.9468 / 0.5214 |
| 155921 | 2020052 / 356479 | 38.2013 / 48.5433 | 0.9463 / 0.5234 | 0.9466 / 0.5187 |
| 181081 | 2020052 / 356479 | 38.2013 / 48.5433 | 0.9467 / 0.5253 | 0.9469 / 0.5197 |
| 206369 | 2020052 / 356479 | 38.2013 / 48.5433 | 0.9465 / 0.5265 | 0.9468 / 0.5216 |

The validation sets each contain 98,060 treated visits and 13,618 control visits,
with 1,921,992 treated non-visits and 342,861 control non-visits.
Predictive diagnostics use different populations: response on treated validation; S factual on all.
AUC/AP do not validate causal uplift ranking. JSON also includes log loss and Brier score.

## Paired uncertainty: S minus response, reference scenario

2,000 paired IID bootstrap replicates per split, compressed into joint ranking-bin × T × Y cells.
Pointwise percentile intervals and simultaneous max-t bands are conditional on fitted models and
fixed original policy memberships. Simultaneous coverage applies only to five reaches within one split
at the reference propensity, not across splits/scenarios. This does not capture refitting, cutoff estimation,
unknown clustering or outcome-stratified sampling uncertainty. Nominal working-model coverage only.

| Seed | Reach | Difference /1,000 | Pointwise 95% | Simultaneous 95% |
|---|---|---:|---:|---:|
| 104729 | 10% | 1.2039 | [0.7646, 1.6248] | [0.6445, 1.7634] |
| 104729 | 20% | 0.4597 | [0.1630, 0.7460] | [0.0884, 0.8310] |
| 104729 | 30% | 0.0366 | [-0.1680, 0.2498] | [-0.2296, 0.3028] |
| 104729 | 40% | 0.0036 | [-0.1724, 0.1891] | [-0.2248, 0.2321] |
| 104729 | 50% | 0.0018 | [-0.1595, 0.1723] | [-0.2072, 0.2108] |
| 130363 | 10% | 1.5734 | [1.1277, 1.9894] | [1.0141, 2.1327] |
| 130363 | 20% | 0.3818 | [0.1224, 0.6518] | [0.0392, 0.7245] |
| 130363 | 30% | 0.1757 | [-0.0135, 0.3584] | [-0.0662, 0.4176] |
| 130363 | 40% | 0.0642 | [-0.0992, 0.2205] | [-0.1477, 0.2761] |
| 130363 | 50% | 0.0642 | [-0.0806, 0.2139] | [-0.1298, 0.2582] |
| 155921 | 10% | 1.0655 | [0.6392, 1.4876] | [0.5231, 1.6078] |
| 155921 | 20% | 0.4068 | [0.0820, 0.7395] | [-0.0067, 0.8202] |
| 155921 | 30% | 0.1916 | [-0.0583, 0.4422] | [-0.1258, 0.5089] |
| 155921 | 40% | 0.1739 | [-0.0362, 0.3785] | [-0.0893, 0.4372] |
| 155921 | 50% | 0.0856 | [-0.0944, 0.2693] | [-0.1466, 0.3179] |
| 181081 | 10% | 1.2615 | [0.8223, 1.6960] | [0.7172, 1.8058] |
| 181081 | 20% | 0.4058 | [0.1053, 0.6995] | [0.0311, 0.7804] |
| 181081 | 30% | 0.1602 | [-0.0517, 0.3738] | [-0.1069, 0.4273] |
| 181081 | 40% | 0.0545 | [-0.1365, 0.2492] | [-0.1896, 0.2985] |
| 181081 | 50% | 0.1177 | [-0.0575, 0.3008] | [-0.0990, 0.3343] |
| 206369 | 10% | 1.1392 | [0.6869, 1.5766] | [0.5732, 1.7053] |
| 206369 | 20% | 0.3053 | [0.0102, 0.5790] | [-0.0640, 0.6746] |
| 206369 | 30% | 0.1503 | [-0.0591, 0.3612] | [-0.1204, 0.4211] |
| 206369 | 40% | -0.0333 | [-0.2162, 0.1355] | [-0.2601, 0.1934] |
| 206369 | 50% | 0.0302 | [-0.1416, 0.1909] | [-0.1833, 0.2437] |

All model-versus-random and S-versus-response pointwise paired contrasts, value/gain intervals,
selected-arm event counts, descriptive selected-arm rate differences and low-support flags are in JSON.

## Propensity sensitivity: mean gain over none /1,000

Scenarios remain separate; changing e can change policy order and does not correct unknown heterogeneity.
This illustrative scenario range is not a validated bound on assignment probabilities or selection bias.

| e assumption | Reach | Random | Response | S-learner |
|---|---|---:|---:|---:|
| 0.8 | 10% | 2.3262 | 17.9289 | 15.8727 |
| 0.8 | 20% | 4.6089 | 21.2784 | 19.8454 |
| 0.8 | 30% | 6.9211 | 22.1116 | 21.2554 |
| 0.8 | 40% | 9.1743 | 22.4854 | 21.7991 |
| 0.8 | 50% | 11.4954 | 22.6584 | 22.0799 |
| 0.825 | 10% | 1.7660 | 13.5159 | 12.9279 |
| 0.825 | 20% | 3.4784 | 16.0572 | 15.4362 |
| 0.825 | 30% | 5.2285 | 16.6613 | 16.2499 |
| 0.825 | 40% | 6.9137 | 16.9401 | 16.5830 |
| 0.825 | 50% | 8.6713 | 17.0594 | 16.7653 |
| 0.85 | 10% | 1.0803 | 8.1106 | 9.3593 |
| 0.85 | 20% | 2.0938 | 9.6625 | 10.0543 |
| 0.85 | 30% | 3.1557 | 9.9850 | 10.1279 |
| 0.85 | 40% | 4.1446 | 10.1473 | 10.1999 |
| 0.85 | 50% | 5.2123 | 10.2005 | 10.2604 |
| 0.875 | 10% | 0.1875 | 1.0683 | 4.7556 |
| 0.875 | 20% | 0.2901 | 1.3319 | 3.0652 |
| 0.875 | 30% | 0.4556 | 1.2864 | 2.1626 |
| 0.875 | 40% | 0.5369 | 1.2969 | 1.8908 |
| 0.875 | 50% | 0.7060 | 1.2632 | 1.7911 |
| 0.9 | 10% | -1.0746 | -8.8935 | -1.7001 |
| 0.9 | 20% | -2.2612 | -10.4513 | -6.7935 |
| 0.9 | 30% | -3.3632 | -11.0188 | -9.0916 |
| 0.9 | 40% | -4.5667 | -11.2233 | -9.8542 |
| 0.9 | 50% | -5.6682 | -11.3804 | -10.1821 |

## Reproducibility and resources

Protocol SHA-256: `61dc75a2d798dceab52f3f1213c2dad2a1a5d3a3108b103b855a1fa2839aada6`.
Source, registry, all memberships, code/protocol hashes, model/prediction hashes and local MLflow run IDs
are recorded in JSON. Sequential execution used two training threads and bounded DuckDB extraction.
Raw data, model files, predictions, caches and local MLflow are ignored by Git.

| Seed | Elapsed seconds | Cumulative process peak RSS GiB | MLflow run |
|---|---:|---:|---|
| 104729 | 190.1 | 3.026 | `285e732fc78b4cf49a9ec7446309ba7a` |
| 130363 | 197.3 | 3.014 | `c00b4ed56af44679af576a09cec9a090` |
| 155921 | 187.3 | 3.020 | `79e3d888848842ac9dc17d994155ed18` |
| 181081 | 182.5 | 3.024 | `6c2a6d06de6c4b1c9a6a6568b0e1bef5` |
| 206369 | 181.7 | 3.024 | `66c860382a4c46e4868929ae9469f36f` |

RSS is a process high-water mark, including earlier splits in the same process; it is not a per-model allocation.
Cloud local files are not guaranteed across new tasks. Restore raw archive with checksum verification,
validate/ingest and reconstruct only missing memberships against the committed registry when needed.
Preserve existing files when present. Private model/prediction/MLflow artifacts require a separate local backup
if future environments must reuse fitted models; Git contains only code and aggregate evidence.
No final winner, optimal reach, business effect or final holdout performance is claimed.

## Measured findings and their limits

At 10% reach, the mean S-minus-response contrast is 1.2487 per 1,000 under e=.85.
The same contrast is -2.0561 under e=.80 and 7.1934 under e=.90.
Its sign reverses across the predeclared scenarios, so causal superiority is not established.
Reference-scenario simultaneous bands exclude zero on the positive side in 5/5
splits at 10% reach and 3/5 at 20%; none do at 30%, 40% or 50%.
Those counts describe overlapping splits, not independent corroborations or a pooled test.
Higher-reach paired uncertainty supports no clear S-versus-response preference under the working model.
The random policy is one frozen realization; bootstrap uncertainty does not resample its seed.
Model refitting uncertainty and probability calibration remain unverified. Platform/library changes
can change fitted artifacts; bitwise reproducibility is checked within this pinned local environment.
