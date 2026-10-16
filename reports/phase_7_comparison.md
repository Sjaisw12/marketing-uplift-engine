# Phase 7 — advanced uplift and robust evaluation

Measured on five frozen development validation partitions. The final holdout remains sealed.
All propensity values are assumptions; neither IPW nor DR establishes causal superiority.
DR requires causal identification plus either correct assignment propensity or both outcome regressions. It does not remove selection bias, hidden experiments, dependence or development-stratification limitations.

## Methods and interpretation

The T-learner reuses each Phase 6 treated-response model and trains one control-arm LightGBM with the same frozen recipe. Both arms receive exactly f0–f11. Scores are m1−m0. Existing response/S/random predictions and all historical results are preserved.
The common DR evaluator averages three training-only fold models per arm. Inner held-fold factual predictions support OOF diagnostics; outer-validation outcomes never enter fitting. All policies share the same evaluator. Saved S-learner m0/m1 supply a separately labeled nuisance sensitivity, not a selected evaluator.
See [the frozen protocol](../docs/PHASE7_PROTOCOL.md) for formulas, seeds, fold definitions, source alignment, full-prefix IPW AUUC/Qini and uncertainty conventions.
All value/gain/contrast numbers below are per 1,000 eligible validation records. Means and ranges across overlapping splits describe stability; they are not independent-replication estimates.

## Reference e=.85: descriptive mean gain over no targeting

| Reach | Evaluator | Random | Response | S | T |
|---|---|---:|---:|---:|---:|
| 10% | IPW | 1.0803 | 8.1106 | 9.3593 | 8.9952 |
| 10% | DR | 0.7581 | 5.2008 | 5.9693 | 5.7731 |
| 20% | IPW | 2.0938 | 9.6625 | 10.0543 | 9.8294 |
| 20% | DR | 1.4525 | 6.7126 | 6.8630 | 6.6526 |
| 30% | IPW | 3.1557 | 9.9850 | 10.1279 | 10.0332 |
| 30% | DR | 2.2158 | 7.0636 | 7.0812 | 6.8848 |
| 40% | IPW | 4.1446 | 10.1473 | 10.1999 | 10.1081 |
| 40% | DR | 2.9708 | 7.2406 | 7.1798 | 6.9691 |
| 50% | IPW | 5.2123 | 10.2005 | 10.2604 | 10.1683 |
| 50% | DR | 3.7438 | 7.3065 | 7.2751 | 7.0298 |

## Per-split reference gains and anchors

| Seed | Method | Reach | Random | Response | S | T | None/all values |
|---|---|---|---:|---:|---:|---:|---:|
| 104729 | ipw | 10% | 1.0297 | 8.1039 | 9.3078 | 8.8989 | 38.2013/48.5433 |
| 104729 | ipw | 20% | 1.8899 | 9.6986 | 10.1583 | 9.7795 | 38.2013/48.5433 |
| 104729 | ipw | 30% | 3.0408 | 10.0303 | 10.0669 | 9.9425 | 38.2013/48.5433 |
| 104729 | ipw | 40% | 4.0025 | 10.2006 | 10.2042 | 10.0233 | 38.2013/48.5433 |
| 104729 | ipw | 50% | 5.0464 | 10.2377 | 10.2395 | 10.1073 | 38.2013/48.5433 |
| 104729 | dr | 10% | 0.6844 | 5.2527 | 5.9924 | 5.7650 | 40.4757/47.9320 |
| 104729 | dr | 20% | 1.2785 | 6.7532 | 6.9458 | 6.6385 | 40.4757/47.9320 |
| 104729 | dr | 30% | 2.0964 | 7.1128 | 7.0276 | 6.8698 | 40.4757/47.9320 |
| 104729 | dr | 40% | 2.8359 | 7.2983 | 7.1625 | 6.9476 | 40.4757/47.9320 |
| 104729 | dr | 50% | 3.5490 | 7.3471 | 7.2260 | 7.0295 | 40.4757/47.9320 |
| 130363 | ipw | 10% | 1.0152 | 8.0843 | 9.6577 | 9.1110 | 38.2013/48.5433 |
| 130363 | ipw | 20% | 2.1323 | 9.4994 | 9.8813 | 9.9890 | 38.2013/48.5433 |
| 130363 | ipw | 30% | 3.2806 | 9.8872 | 10.0629 | 10.2869 | 38.2013/48.5433 |
| 130363 | ipw | 40% | 4.2892 | 10.0880 | 10.1522 | 10.4311 | 38.2013/48.5433 |
| 130363 | ipw | 50% | 5.4182 | 10.1860 | 10.2502 | 10.4943 | 38.2013/48.5433 |
| 130363 | dr | 10% | 0.7638 | 5.1179 | 6.1022 | 5.8225 | 40.4986/47.9288 |
| 130363 | dr | 20% | 1.4995 | 6.5362 | 6.7143 | 6.7042 | 40.4986/47.9288 |
| 130363 | dr | 30% | 2.3826 | 6.9483 | 6.9856 | 7.0147 | 40.4986/47.9288 |
| 130363 | dr | 40% | 3.2288 | 7.1612 | 7.1114 | 7.1820 | 40.4986/47.9288 |
| 130363 | dr | 50% | 3.9536 | 7.2696 | 7.2302 | 7.2347 | 40.4986/47.9288 |
| 155921 | ipw | 10% | 1.1452 | 8.0523 | 9.1178 | 8.7886 | 38.2013/48.5433 |
| 155921 | ipw | 20% | 2.1389 | 9.6854 | 10.0922 | 9.8044 | 38.2013/48.5433 |
| 155921 | ipw | 30% | 3.0897 | 10.0461 | 10.2377 | 10.0029 | 38.2013/48.5433 |
| 155921 | ipw | 40% | 4.2411 | 10.1479 | 10.3218 | 10.0248 | 38.2013/48.5433 |
| 155921 | ipw | 50% | 5.3174 | 10.1953 | 10.2809 | 10.0303 | 38.2013/48.5433 |
| 155921 | dr | 10% | 0.7193 | 5.2448 | 5.8583 | 5.6856 | 40.3660/47.9546 |
| 155921 | dr | 20% | 1.4222 | 6.8717 | 6.9825 | 6.7676 | 40.3660/47.9546 |
| 155921 | dr | 30% | 2.1555 | 7.2620 | 7.3216 | 7.0393 | 40.3660/47.9546 |
| 155921 | dr | 40% | 3.0501 | 7.3770 | 7.4382 | 7.0726 | 40.3660/47.9546 |
| 155921 | dr | 50% | 3.8863 | 7.4377 | 7.4720 | 7.0849 | 40.3660/47.9546 |
| 181081 | ipw | 10% | 1.1945 | 8.1250 | 9.3866 | 9.0885 | 38.2013/48.5433 |
| 181081 | ipw | 20% | 2.1422 | 9.7504 | 10.1562 | 9.8836 | 38.2013/48.5433 |
| 181081 | ipw | 30% | 3.2927 | 10.0616 | 10.2219 | 10.0763 | 38.2013/48.5433 |
| 181081 | ipw | 40% | 4.3045 | 10.2050 | 10.2595 | 10.1728 | 38.2013/48.5433 |
| 181081 | ipw | 50% | 5.2588 | 10.2174 | 10.3351 | 10.2459 | 38.2013/48.5433 |
| 181081 | dr | 10% | 0.8919 | 5.2313 | 6.0002 | 5.7928 | 40.4764/47.9262 |
| 181081 | dr | 20% | 1.5510 | 6.7865 | 6.8915 | 6.7029 | 40.4764/47.9262 |
| 181081 | dr | 30% | 2.2838 | 7.1367 | 7.1365 | 6.8728 | 40.4764/47.9262 |
| 181081 | dr | 40% | 2.9906 | 7.2977 | 7.2016 | 6.9818 | 40.4764/47.9262 |
| 181081 | dr | 50% | 3.7289 | 7.3221 | 7.3132 | 7.0410 | 40.4764/47.9262 |
| 206369 | ipw | 10% | 1.0170 | 8.1874 | 9.3267 | 9.0890 | 38.2013/48.5433 |
| 206369 | ipw | 20% | 2.1658 | 9.6785 | 9.9837 | 9.6903 | 38.2013/48.5433 |
| 206369 | ipw | 30% | 3.0745 | 9.8997 | 10.0501 | 9.8573 | 38.2013/48.5433 |
| 206369 | ipw | 40% | 3.8859 | 10.0951 | 10.0618 | 9.8885 | 38.2013/48.5433 |
| 206369 | ipw | 50% | 5.0207 | 10.1659 | 10.1961 | 9.9638 | 38.2013/48.5433 |
| 206369 | dr | 10% | 0.7308 | 5.1571 | 5.8936 | 5.7998 | 40.5780/47.9154 |
| 206369 | dr | 20% | 1.5113 | 6.6153 | 6.7811 | 6.4500 | 40.5780/47.9154 |
| 206369 | dr | 30% | 2.1609 | 6.8581 | 6.9346 | 6.6274 | 40.5780/47.9154 |
| 206369 | dr | 40% | 2.7487 | 7.0687 | 6.9852 | 6.6615 | 40.5780/47.9154 |
| 206369 | dr | 50% | 3.6010 | 7.1560 | 7.1342 | 6.7588 | 40.5780/47.9154 |

## Paired T-minus-S reference contrasts

2,000 correlated Gaussian-multiplier replicates use the full joint covariance recovered from continuous within-cell moments. This is not an exact ordinary row bootstrap. Intervals are nominal IID working-model intervals, conditional on fitted models, nuisance predictions, fixed rankings and targeting memberships. No refitting, reranking, cluster correction or stratification correction is included.
Pointwise intervals use multiplier quantiles. Simultaneous bands cover the predeclared ten comparisons (five reaches × IPW/DR) within each split at e=.85. They do not adjust across splits, other policy contrasts, propensity scenarios or nuisance alternatives.

| Seed | Method | Reach | Difference | Pointwise 95% | Simultaneous 95% |
|---|---|---|---:|---:|---:|
| 104729 | ipw | 10% | -0.4089 | [-0.7517, -0.0982] | [-0.8330, 0.0152] |
| 104729 | ipw | 20% | -0.3789 | [-0.7157, -0.0579] | [-0.8105, 0.0528] |
| 104729 | ipw | 30% | -0.1244 | [-0.4372, 0.1871] | [-0.5503, 0.3015] |
| 104729 | ipw | 40% | -0.1809 | [-0.5011, 0.1399] | [-0.6096, 0.2478] |
| 104729 | ipw | 50% | -0.1322 | [-0.4477, 0.1891] | [-0.5568, 0.2925] |
| 104729 | dr | 10% | -0.2274 | [-0.4831, 0.0119] | [-0.5566, 0.1019] |
| 104729 | dr | 20% | -0.3073 | [-0.5636, -0.0434] | [-0.6533, 0.0386] |
| 104729 | dr | 30% | -0.1578 | [-0.4092, 0.1031] | [-0.5028, 0.1872] |
| 104729 | dr | 40% | -0.2150 | [-0.4722, 0.0497] | [-0.5647, 0.1348] |
| 104729 | dr | 50% | -0.1965 | [-0.4520, 0.0709] | [-0.5413, 0.1482] |
| 130363 | ipw | 10% | -0.5467 | [-0.8537, -0.2179] | [-0.9702, -0.1232] |
| 130363 | ipw | 20% | 0.1078 | [-0.2256, 0.4326] | [-0.3253, 0.5408] |
| 130363 | ipw | 30% | 0.2239 | [-0.0995, 0.5287] | [-0.1971, 0.6450] |
| 130363 | ipw | 40% | 0.2789 | [-0.0439, 0.5870] | [-0.1413, 0.6990] |
| 130363 | ipw | 50% | 0.2441 | [-0.0829, 0.5581] | [-0.1713, 0.6594] |
| 130363 | dr | 10% | -0.2797 | [-0.5192, -0.0301] | [-0.6048, 0.0453] |
| 130363 | dr | 20% | -0.0100 | [-0.2716, 0.2406] | [-0.3544, 0.3343] |
| 130363 | dr | 30% | 0.0292 | [-0.2256, 0.2655] | [-0.3120, 0.3703] |
| 130363 | dr | 40% | 0.0706 | [-0.1972, 0.3075] | [-0.2712, 0.4124] |
| 130363 | dr | 50% | 0.0045 | [-0.2650, 0.2447] | [-0.3316, 0.3407] |
| 155921 | ipw | 10% | -0.3292 | [-0.6418, -0.0518] | [-0.7421, 0.0837] |
| 155921 | ipw | 20% | -0.2878 | [-0.6045, 0.0339] | [-0.7282, 0.1527] |
| 155921 | ipw | 30% | -0.2348 | [-0.5507, 0.0802] | [-0.6669, 0.1972] |
| 155921 | ipw | 40% | -0.2970 | [-0.6204, 0.0160] | [-0.7283, 0.1343] |
| 155921 | ipw | 50% | -0.2507 | [-0.5682, 0.0591] | [-0.6721, 0.1708] |
| 155921 | dr | 10% | -0.1727 | [-0.4189, 0.0559] | [-0.4936, 0.1482] |
| 155921 | dr | 20% | -0.2149 | [-0.4697, 0.0378] | [-0.5649, 0.1352] |
| 155921 | dr | 30% | -0.2823 | [-0.5369, -0.0387] | [-0.6307, 0.0662] |
| 155921 | dr | 40% | -0.3656 | [-0.6259, -0.1150] | [-0.7143, -0.0169] |
| 155921 | dr | 50% | -0.3872 | [-0.6404, -0.1437] | [-0.7260, -0.0483] |
| 181081 | ipw | 10% | -0.2980 | [-0.6135, 0.0178] | [-0.7152, 0.1192] |
| 181081 | ipw | 20% | -0.2726 | [-0.6048, 0.0653] | [-0.7167, 0.1715] |
| 181081 | ipw | 30% | -0.1455 | [-0.4759, 0.1870] | [-0.5854, 0.2943] |
| 181081 | ipw | 40% | -0.0866 | [-0.4139, 0.2474] | [-0.5257, 0.3525] |
| 181081 | ipw | 50% | -0.0891 | [-0.4120, 0.2443] | [-0.5250, 0.3468] |
| 181081 | dr | 10% | -0.2074 | [-0.4519, 0.0227] | [-0.5300, 0.1153] |
| 181081 | dr | 20% | -0.1886 | [-0.4687, 0.0785] | [-0.5416, 0.1643] |
| 181081 | dr | 30% | -0.2637 | [-0.5306, 0.0094] | [-0.6182, 0.0908] |
| 181081 | dr | 40% | -0.2198 | [-0.4963, 0.0494] | [-0.5762, 0.1366] |
| 181081 | dr | 50% | -0.2722 | [-0.5494, -0.0024] | [-0.6246, 0.0803] |
| 206369 | ipw | 10% | -0.2376 | [-0.5509, 0.0574] | [-0.6523, 0.1771] |
| 206369 | ipw | 20% | -0.2934 | [-0.6025, 0.0254] | [-0.7149, 0.1281] |
| 206369 | ipw | 30% | -0.1927 | [-0.4960, 0.1131] | [-0.6067, 0.2212] |
| 206369 | ipw | 40% | -0.1733 | [-0.4734, 0.1336] | [-0.5859, 0.2394] |
| 206369 | ipw | 50% | -0.2323 | [-0.5359, 0.0650] | [-0.6396, 0.1749] |
| 206369 | dr | 10% | -0.0938 | [-0.3401, 0.1477] | [-0.4142, 0.2265] |
| 206369 | dr | 20% | -0.3311 | [-0.5883, -0.0661] | [-0.6747, 0.0126] |
| 206369 | dr | 30% | -0.3072 | [-0.5585, -0.0482] | [-0.6456, 0.0312] |
| 206369 | dr | 40% | -0.3237 | [-0.5767, -0.0666] | [-0.6617, 0.0143] |
| 206369 | dr | 50% | -0.3754 | [-0.6181, -0.1276] | [-0.7085, -0.0423] |

## Propensity and nuisance sensitivity: mean T-minus-S

Each scenario is separate. The range is illustrative, not a validated bound on propensity or bias. S-nuisance DR has point estimates only and is not selected based on favorable performance.

| e | Reach | IPW | Shared cross-fit DR | S-nuisance DR |
|---|---|---:|---:|---:|
| 0.8 | 10% | -0.0698 | -0.1396 | -0.2332 |
| 0.8 | 20% | -1.0503 | -0.1707 | -0.2599 |
| 0.8 | 30% | -1.6121 | -0.1679 | -0.2589 |
| 0.8 | 40% | -1.8616 | -0.1782 | -0.2726 |
| 0.8 | 50% | -1.9385 | -0.2073 | -0.3017 |
| 0.825 | 10% | -0.1995 | -0.1632 | -0.2160 |
| 0.825 | 20% | -0.6813 | -0.1865 | -0.2341 |
| 0.825 | 30% | -0.9351 | -0.1788 | -0.2267 |
| 0.825 | 40% | -1.0721 | -0.1908 | -0.2405 |
| 0.825 | 50% | -1.1148 | -0.2223 | -0.2719 |
| 0.85 | 10% | -0.3641 | -0.1962 | -0.1936 |
| 0.85 | 20% | -0.2250 | -0.2104 | -0.2017 |
| 0.85 | 30% | -0.0947 | -0.1963 | -0.1861 |
| 0.85 | 40% | -0.0918 | -0.2107 | -0.1999 |
| 0.85 | 50% | -0.0920 | -0.2453 | -0.2344 |
| 0.875 | 10% | -0.5855 | -0.2441 | -0.1627 |
| 0.875 | 20% | 0.3748 | -0.2470 | -0.1583 |
| 0.875 | 30% | 1.0135 | -0.2243 | -0.1315 |
| 0.875 | 40% | 1.2012 | -0.2420 | -0.1455 |
| 0.875 | 50% | 1.2570 | -0.2812 | -0.1845 |
| 0.9 | 10% | -0.9074 | -0.3180 | -0.1172 |
| 0.9 | 20% | 1.2297 | -0.3056 | -0.0956 |
| 0.9 | 30% | 2.5976 | -0.2702 | -0.0525 |
| 0.9 | 40% | 3.0495 | -0.2928 | -0.0667 |
| 0.9 | 50% | 3.1855 | -0.3389 | -0.1127 |

## Support and calibration

Each validation partition contains 2,020,052 treated records/98,060 visits and 356,479 controls/13,618 visits. JSON contains arm/event counts for every policy at cumulative and disjoint reaches, absent-arm handling and control-visits<30 warnings.
Calibration bins are fixed before performance examination. Diagnostics below concern factual outcome probabilities, not individual-effect accuracy. Full fixed-bin reliability counts, log loss, Brier, AUC and AP are in JSON. No calibration transformation was fitted.

| Seed | Predictor/population | Log loss | Brier | AUC | AP |
|---|---|---:|---:|---:|---:|
| 104729 | t_arm_0 | 0.089582 | 0.025386 | 0.946823 | 0.479257 |
| 104729 | dr_arm_0 | 0.089594 | 0.025390 | 0.946826 | 0.478759 |
| 104729 | oof_arm_0 | 0.089470 | 0.025448 | 0.947496 | 0.477260 |
| 104729 | s_arm_0 | 0.089580 | 0.025388 | 0.946864 | 0.478891 |
| 104729 | t_arm_1 | 0.105492 | 0.030564 | 0.946343 | 0.522508 |
| 104729 | dr_arm_1 | 0.105476 | 0.030557 | 0.946355 | 0.522634 |
| 104729 | oof_arm_1 | 0.105268 | 0.030490 | 0.946471 | 0.524780 |
| 104729 | s_arm_1 | 0.105501 | 0.030565 | 0.946323 | 0.522547 |
| 130363 | t_arm_0 | 0.088839 | 0.025248 | 0.948360 | 0.485530 |
| 130363 | dr_arm_0 | 0.088791 | 0.025231 | 0.948387 | 0.486271 |
| 130363 | oof_arm_0 | 0.089646 | 0.025483 | 0.947174 | 0.475993 |
| 130363 | s_arm_0 | 0.088820 | 0.025245 | 0.948454 | 0.485606 |
| 130363 | t_arm_1 | 0.105146 | 0.030422 | 0.946476 | 0.526464 |
| 130363 | dr_arm_1 | 0.105137 | 0.030420 | 0.946492 | 0.526460 |
| 130363 | oof_arm_1 | 0.105355 | 0.030526 | 0.946437 | 0.523856 |
| 130363 | s_arm_1 | 0.105176 | 0.030432 | 0.946445 | 0.526158 |
| 155921 | t_arm_0 | 0.089346 | 0.025364 | 0.947438 | 0.481431 |
| 155921 | dr_arm_0 | 0.089314 | 0.025357 | 0.947527 | 0.481780 |
| 155921 | oof_arm_0 | 0.089527 | 0.025448 | 0.947309 | 0.476927 |
| 155921 | s_arm_0 | 0.089342 | 0.025369 | 0.947561 | 0.481726 |
| 155921 | t_arm_1 | 0.105369 | 0.030517 | 0.946310 | 0.523446 |
| 155921 | dr_arm_1 | 0.105354 | 0.030513 | 0.946334 | 0.523675 |
| 155921 | oof_arm_1 | 0.105292 | 0.030501 | 0.946477 | 0.524605 |
| 155921 | s_arm_1 | 0.105364 | 0.030514 | 0.946309 | 0.523614 |
| 181081 | t_arm_0 | 0.089521 | 0.025413 | 0.947085 | 0.476492 |
| 181081 | dr_arm_0 | 0.089497 | 0.025405 | 0.947109 | 0.476810 |
| 181081 | oof_arm_0 | 0.089445 | 0.025431 | 0.947534 | 0.478972 |
| 181081 | s_arm_0 | 0.089508 | 0.025408 | 0.947158 | 0.476927 |
| 181081 | t_arm_1 | 0.105101 | 0.030457 | 0.946740 | 0.525297 |
| 181081 | dr_arm_1 | 0.105071 | 0.030449 | 0.946782 | 0.525543 |
| 181081 | oof_arm_1 | 0.105351 | 0.030512 | 0.946375 | 0.524329 |
| 181081 | s_arm_1 | 0.105118 | 0.030461 | 0.946711 | 0.525340 |
| 206369 | t_arm_0 | 0.089272 | 0.025371 | 0.948003 | 0.483655 |
| 206369 | dr_arm_0 | 0.089260 | 0.025368 | 0.947983 | 0.483719 |
| 206369 | oof_arm_0 | 0.089523 | 0.025446 | 0.947246 | 0.476830 |
| 206369 | s_arm_0 | 0.089220 | 0.025360 | 0.948032 | 0.483690 |
| 206369 | t_arm_1 | 0.105160 | 0.030440 | 0.946486 | 0.526525 |
| 206369 | dr_arm_1 | 0.105147 | 0.030432 | 0.946497 | 0.526788 |
| 206369 | oof_arm_1 | 0.105362 | 0.030524 | 0.946405 | 0.523821 |
| 206369 | s_arm_1 | 0.105164 | 0.030434 | 0.946459 | 0.526704 |

### Control event support across splits

Minima are descriptive across the five overlapping splits. Flags use the predeclared <30 control-visits threshold in disjoint bands.

| Reach | Ranking | Minimum cumulative control n | Minimum cumulative control visits | Minimum band control visits | Flagged bands /5 |
|---|---|---:|---:|---:|---:|
| 10% | random | 35525 | 1317 | 1317 | 0 |
| 10% | response | 32889 | 10594 | 10594 | 0 |
| 10% | s_learner | 31658 | 6673 | 6673 | 0 |
| 10% | t_learner | 31774 | 7015 | 7015 | 0 |
| 20% | random | 70901 | 2689 | 1346 | 0 |
| 20% | response | 67967 | 12532 | 1888 | 0 |
| 20% | s_learner | 67211 | 9818 | 3052 | 0 |
| 20% | t_learner | 67429 | 9382 | 2319 | 0 |
| 30% | random | 106551 | 3990 | 1301 | 0 |
| 30% | response | 103945 | 13100 | 529 | 0 |
| 30% | s_learner | 103401 | 11456 | 1311 | 0 |
| 30% | t_learner | 103559 | 10088 | 692 | 0 |
| 40% | random | 142165 | 5392 | 1287 | 0 |
| 40% | response | 140175 | 13337 | 215 | 0 |
| 40% | s_learner | 139875 | 12191 | 430 | 0 |
| 40% | t_learner | 139895 | 10322 | 232 | 0 |
| 50% | random | 178031 | 6735 | 1336 | 0 |
| 50% | response | 176805 | 13475 | 123 | 0 |
| 50% | s_learner | 176400 | 12555 | 160 | 0 |
| 50% | t_learner | 176253 | 10483 | 146 | 0 |

### First-split control calibration illustration

The full bin tables for every split and arm are retained in JSON; bin boundaries were frozen before evaluation.

| Predictor | Probability bin | Records | Observed visit rate | Mean prediction |
|---|---|---:|---:|---:|
| t_arm_0 | 0.0–0.01 | 254864 | 0.00208 | 0.00206 |
| t_arm_0 | 0.01–0.02 | 27107 | 0.01476 | 0.01456 |
| t_arm_0 | 0.02–0.05 | 25882 | 0.03133 | 0.03147 |
| t_arm_0 | 0.05–0.1 | 13196 | 0.07510 | 0.07170 |
| t_arm_0 | 0.1–0.2 | 12633 | 0.13330 | 0.14229 |
| t_arm_0 | 0.2–0.4 | 12610 | 0.29104 | 0.28935 |
| t_arm_0 | 0.4–0.6 | 7448 | 0.49006 | 0.48853 |
| t_arm_0 | 0.6–0.8 | 2585 | 0.67737 | 0.67720 |
| t_arm_0 | 0.8–1.0 | 154 | 0.84416 | 0.82604 |
| dr_arm_0 | 0.0–0.01 | 254587 | 0.00205 | 0.00206 |
| dr_arm_0 | 0.01–0.02 | 27334 | 0.01460 | 0.01445 |
| dr_arm_0 | 0.02–0.05 | 25961 | 0.03197 | 0.03151 |
| dr_arm_0 | 0.05–0.1 | 13182 | 0.07336 | 0.07165 |
| dr_arm_0 | 0.1–0.2 | 12592 | 0.13612 | 0.14274 |
| dr_arm_0 | 0.2–0.4 | 12635 | 0.28864 | 0.28930 |
| dr_arm_0 | 0.4–0.6 | 7468 | 0.49210 | 0.48865 |
| dr_arm_0 | 0.6–0.8 | 2586 | 0.67633 | 0.67575 |
| dr_arm_0 | 0.8–1.0 | 134 | 0.86567 | 0.81904 |
| s_arm_0 | 0.0–0.01 | 253572 | 0.00201 | 0.00214 |
| s_arm_0 | 0.01–0.02 | 26147 | 0.01411 | 0.01443 |
| s_arm_0 | 0.02–0.05 | 27547 | 0.02991 | 0.03128 |
| s_arm_0 | 0.05–0.1 | 13950 | 0.07362 | 0.07191 |
| s_arm_0 | 0.1–0.2 | 12372 | 0.13611 | 0.14295 |
| s_arm_0 | 0.2–0.4 | 12938 | 0.28953 | 0.28967 |
| s_arm_0 | 0.4–0.6 | 7104 | 0.49381 | 0.48828 |
| s_arm_0 | 0.6–0.8 | 2711 | 0.67872 | 0.67693 |
| s_arm_0 | 0.8–1.0 | 138 | 0.80435 | 0.82377 |

## Repeated vectors and dependence

Exact equality of all twelve features defines a vector, not a customer. No deduplication or membership changes were made. Overlap may reflect distinct anonymous records and cannot justify an entity-cluster correction.

| Seed | Shared distinct vectors | Validation rows matching training | Share |
|---|---:|---:|---:|
| 104729 | 338776 | 368915 | 15.5233% |
| 130363 | 339545 | 369936 | 15.5662% |
| 155921 | 338975 | 369089 | 15.5306% |
| 181081 | 339858 | 370360 | 15.5841% |
| 206369 | 338690 | 368580 | 15.5092% |

## Resources and reproducibility

Protocol SHA-256: `f3201b0fad04191b48607f269d1d1e1a3d25ef0203f6df06c7f1578881eee83e`.
All five auxiliary fold files were hashed before first execution; fit manifests hash models/predictions before evaluation. Phase 6 models, predictions, MLflow runs, frozen protocol, reports, lockfile and memberships remain unchanged.
Sequential two-thread fits, one-thread bounded DuckDB, batched predictions and streaming moments avoid a rows × 2,000 replicate matrix. Peak RSS is a process high-water mark, potentially including earlier splits.

| Seed | New fitted models | Elapsed seconds | Peak process RSS GiB | Joint cells | MLflow run |
|---|---:|---:|---:|---:|---|
| 104729 | 7 | 280.92 | 3.736 | 947 | `9f7a5bbbf4004702a1e71819f561451e` |
| 130363 | 7 | 289.31 | 3.718 | 940 | `3135d485f0ed4119b0bd787e015f8f6d` |
| 155921 | 7 | 281.90 | 3.718 | 941 | `ab8f5c37b6904711b07063b3c901ccec` |
| 181081 | 7 | 281.03 | 3.730 | 951 | `c2b40a287e414b7c87528f9b2c5da64e` |
| 206369 | 7 | 288.15 | 3.730 | 939 | `97e749355c76415a9eb10fb17205e8cf` |

Models, predictions, OOF records, nuisance folds and MLflow remain ignored by Git. Cloud local artifacts are not guaranteed to persist into another task; preserve private artifacts separately if needed. Reuse matching existing inputs rather than recreating them.
The five development splits overlap and already informed earlier development; these are further development comparisons, not a fresh confirmatory test. Calibration cannot validate exchangeability or selection assumptions. Unknown individual/experiment dependence remains unresolved.
No final model/reach, causal superiority, advertiser-wide effect, ROI, abstention decision or holdout result is claimed.


## Measured interpretation

At reference e=.85 and 10% reach, mean T-minus-S is -0.3641 per1,000 with IPW and -0.1962 with the common DR evaluator.
The T-learner's mean contrast is negative at every reference reach under both evaluators. Separate arm models do not guarantee better uplift ranking; the control arm is smaller and subtracting two response predictions can amplify estimation error.
Across the 50 within-split simultaneous bands, 0 lie wholly above zero and 4 wholly below zero; the others contain zero. These are descriptive counts over overlapping splits, not independent confirmations or a pooled test.
At 40% and 50% reference reach, the mean response-versus-S order differs between IPW and DR. Evaluator agreement cannot be presumed, and no favorable metric is selected.
All disjoint reach bands have more than 30 control visits (minimum123 in the measured runs); no low-control-event warning is triggered. These counts do not remove unknown dependence or privacy-selection limitations.
Control factual discrimination is strong (mean T-arm ROC AUC about .9475), but outcome discrimination and calibration do not validate individual treatment effects or causal identification.
All reference T-versus-S means remain negative with the alternative S nuisance. This limited nuisance agreement does not establish correctness of either evaluator. The full propensity/nuisance grid remains assumption-dependent.
