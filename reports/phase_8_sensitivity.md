# Phase 8 — propensity, nuisance and marginal evidence

All monetary inputs are hypothetical currency units, not observed Criteo costs,
revenue, ROI or savings. Values below are assumption-dependent released-development
benchmark estimates, not proven causal or financial improvements. Propensities are
assumptions; DR does not repair unknown experiment assignment, privacy selection or
unverified identification. Gaussian intervals are nominal IID working-model,
conditional on fitted models and fixed role-specific policies, excluding refitting,
unknown dependence and outcome-stratification uncertainty. Pointwise intervals differ
from the one-sided simultaneous 300-coordinate marginal decision bounds. Splits overlap;
mean/range and decision frequencies are descriptive, not independent replications.
Auxiliary assessment roles reduce direct selection reuse but are not fresh confirmatory
data: development outcomes informed prior phases. No deployment policy is selected or
locked, and the final holdout remains sealed.

The next table reports selection first-tranche gain/1,000 ranges across all 15 assumptions, and the worst simultaneous lower bound.
No probabilities are assigned to scenarios. IPW, primary DR and saved-S-nuisance DR remain separate.

| Split | Ranking | First-tranche point range/1,000 | Worst lower/1,000 |
|---|---|---|---:|
| 104729 | random | [-1.0071, 2.3438] | -1.6884 |
| 104729 | response | [-8.7588, 17.9863] | -10.6851 |
| 104729 | s_learner | [-1.2511, 16.0286] | -2.7875 |
| 104729 | t_learner | [-2.6154, 15.7036] | -4.2007 |
| 130363 | random | [-1.0679, 2.2859] | -1.7314 |
| 130363 | response | [-8.7317, 18.0852] | -10.6082 |
| 130363 | s_learner | [-1.7523, 16.3695] | -3.2842 |
| 130363 | t_learner | [-2.7959, 16.0633] | -4.3611 |
| 155921 | random | [-0.9407, 2.4237] | -1.6349 |
| 155921 | response | [-9.3984, 17.5824] | -11.3682 |
| 155921 | s_learner | [-1.9767, 15.6752] | -3.5586 |
| 155921 | t_learner | [-2.8566, 15.6583] | -4.4788 |
| 181081 | random | [-0.7107, 2.5562] | -1.3698 |
| 181081 | response | [-9.5115, 17.6392] | -11.4193 |
| 181081 | s_learner | [-2.0431, 15.6057] | -3.5703 |
| 181081 | t_learner | [-2.8305, 15.5195] | -4.3895 |
| 206369 | random | [-1.2605, 2.2691] | -1.9521 |
| 206369 | response | [-7.7947, 18.4818] | -9.6783 |
| 206369 | s_learner | [-1.7065, 15.6846] | -3.2296 |
| 206369 | t_learner | [-2.1076, 16.0539] | -3.6650 |

## Evaluator sensitivity at 10% reach

Selection gain ranges across the five assumed propensities, per 1,000 eligible records. These are stress ranges, not confidence intervals.

| Split | Ranking | Evaluator | Point range/1,000 |
|---|---|---|---|
| 104729 | random | ipw | [-1.0071, 2.3438] |
| 104729 | random | dr | [0.5752, 0.6278] |
| 104729 | random | s_dr | [0.5828, 0.6180] |
| 104729 | response | ipw | [-8.7588, 17.9863] |
| 104729 | response | dr | [4.9729, 5.1365] |
| 104729 | response | s_dr | [4.9461, 5.0814] |
| 104729 | s_learner | ipw | [-1.2511, 16.0286] |
| 104729 | s_learner | dr | [6.1207, 6.1276] |
| 104729 | s_learner | s_dr | [6.0504, 6.1049] |
| 104729 | t_learner | ipw | [-2.6154, 15.7036] |
| 104729 | t_learner | dr | [5.4758, 5.8177] |
| 104729 | t_learner | s_dr | [5.6435, 5.6741] |
| 130363 | random | ipw | [-1.0679, 2.2859] |
| 130363 | random | dr | [0.7254, 0.7814] |
| 130363 | random | s_dr | [0.7130, 0.7837] |
| 130363 | response | ipw | [-8.7317, 18.0852] |
| 130363 | response | dr | [5.1181, 5.2296] |
| 130363 | response | s_dr | [5.0382, 5.1518] |
| 130363 | s_learner | ipw | [-1.7523, 16.3695] |
| 130363 | s_learner | dr | [5.8633, 6.0041] |
| 130363 | s_learner | s_dr | [5.8023, 5.8992] |
| 130363 | t_learner | ipw | [-2.7959, 16.0633] |
| 130363 | t_learner | dr | [5.5037, 5.8411] |
| 130363 | t_learner | s_dr | [5.6272, 5.6582] |
| 155921 | random | ipw | [-0.9407, 2.4237] |
| 155921 | random | dr | [0.7766, 0.8131] |
| 155921 | random | s_dr | [0.7645, 0.8175] |
| 155921 | response | ipw | [-9.3984, 17.5824] |
| 155921 | response | dr | [5.3648, 5.4516] |
| 155921 | response | s_dr | [5.3074, 5.4031] |
| 155921 | s_learner | ipw | [-1.9767, 15.6752] |
| 155921 | s_learner | dr | [6.0543, 6.1668] |
| 155921 | s_learner | s_dr | [6.0015, 6.0809] |
| 155921 | t_learner | ipw | [-2.8566, 15.6583] |
| 155921 | t_learner | dr | [5.7400, 5.9624] |
| 155921 | t_learner | s_dr | [5.7979, 5.8912] |
| 181081 | random | ipw | [-0.7107, 2.5562] |
| 181081 | random | dr | [0.9185, 1.0290] |
| 181081 | random | s_dr | [0.9114, 1.0405] |
| 181081 | response | ipw | [-9.5115, 17.6392] |
| 181081 | response | dr | [4.8187, 5.1664] |
| 181081 | response | s_dr | [4.7670, 5.1006] |
| 181081 | s_learner | ipw | [-2.0431, 15.6057] |
| 181081 | s_learner | dr | [5.7655, 5.9975] |
| 181081 | s_learner | s_dr | [5.7307, 5.9143] |
| 181081 | t_learner | ipw | [-2.8305, 15.5195] |
| 181081 | t_learner | dr | [5.4599, 5.8419] |
| 181081 | t_learner | s_dr | [5.6335, 5.6675] |
| 206369 | random | ipw | [-1.2605, 2.2691] |
| 206369 | random | dr | [0.6908, 0.7394] |
| 206369 | random | s_dr | [0.6760, 0.7183] |
| 206369 | response | ipw | [-7.7947, 18.4818] |
| 206369 | response | dr | [5.5164, 5.7590] |
| 206369 | response | s_dr | [5.4101, 5.6724] |
| 206369 | s_learner | ipw | [-1.7065, 15.6846] |
| 206369 | s_learner | dr | [5.9805, 6.0310] |
| 206369 | s_learner | s_dr | [5.9246, 5.9286] |
| 206369 | t_learner | ipw | [-2.1076, 16.0539] |
| 206369 | t_learner | dr | [5.8633, 6.0019] |
| 206369 | t_learner | s_dr | [5.7861, 6.0146] |

## Support and limitations

- Split 104729 selection: minimum tranche control visits 68; inadequate-support tranches 0/20. Assessment warnings do not change decisions.
- Split 104729 assessment: minimum tranche control visits 65; inadequate-support tranches 0/20. Assessment warnings do not change decisions.
- Split 130363 selection: minimum tranche control visits 54; inadequate-support tranches 0/20. Assessment warnings do not change decisions.
- Split 130363 assessment: minimum tranche control visits 72; inadequate-support tranches 0/20. Assessment warnings do not change decisions.
- Split 155921 selection: minimum tranche control visits 68; inadequate-support tranches 0/20. Assessment warnings do not change decisions.
- Split 155921 assessment: minimum tranche control visits 63; inadequate-support tranches 0/20. Assessment warnings do not change decisions.
- Split 181081 selection: minimum tranche control visits 72; inadequate-support tranches 0/20. Assessment warnings do not change decisions.
- Split 181081 assessment: minimum tranche control visits 75; inadequate-support tranches 0/20. Assessment warnings do not change decisions.
- Split 206369 selection: minimum tranche control visits 62; inadequate-support tranches 0/20. Assessment warnings do not change decisions.
- Split 206369 assessment: minimum tranche control visits 61; inadequate-support tranches 0/20. Assessment warnings do not change decisions.

Worst-case aggregation can abstain because one assumed propensity makes even the first tranche negative; increasing hypothetical visit value cannot repair a negative visit-gain bound.
Any zero recommendation concerns the declared grid and stress objective. It does not prove all smaller campaigns, all models or the real population have nonpositive effects.
If identification or dependence assumptions cannot be justified, use these outputs as scenario analysis and withhold an operational spending recommendation.
