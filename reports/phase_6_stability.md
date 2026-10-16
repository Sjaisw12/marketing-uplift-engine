# Phase 6 — descriptive development stability

Five validation sets overlap; no independent-replication confidence interval is computed.
Ranks below are based on reference-scenario point estimates, not statistically declared winners.

| Reach | Random first | Response first | S first | Point-estimate orders by split |
|---|---:|---:|---:|---|
| 10% | 0 | 0 | 5 | s_learner>response>random; s_learner>response>random; s_learner>response>random; s_learner>response>random; s_learner>response>random |
| 20% | 0 | 0 | 5 | s_learner>response>random; s_learner>response>random; s_learner>response>random; s_learner>response>random; s_learner>response>random |
| 30% | 0 | 0 | 5 | s_learner>response>random; s_learner>response>random; s_learner>response>random; s_learner>response>random; s_learner>response>random |
| 40% | 0 | 1 | 4 | s_learner>response>random; s_learner>response>random; s_learner>response>random; s_learner>response>random; response>s_learner>random |
| 50% | 0 | 0 | 5 | s_learner>response>random; s_learner>response>random; s_learner>response>random; s_learner>response>random; s_learner>response>random |

## Full-prefix ranking areas: reference-scenario means [ranges]

| Model | IPW AUUC | IPW Qini area |
|---|---:|---:|
| random | 0.00521174 [0.00511267, 0.00532747] | 0.00004075 [-0.00005832, 0.00015648] |
| response | 0.00958410 [0.00955577, 0.00961562] | 0.00441311 [0.00438478, 0.00444463] |
| s_learner | 0.00989929 [0.00985489, 0.00998002] | 0.00472830 [0.00468390, 0.00480903] |

Differences may reflect membership and fitted-model variation. Small or overlapping paired bands
support no clear preference under that scenario. Assumption sensitivity can dominate sampling intervals.
No model or reach is selected for final evaluation in this phase.
