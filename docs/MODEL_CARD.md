# Model and decision-system card

| Item | Specification |
|---|---|
| Intended use | Offline educational comparison of assignment-level targeting strategies on the released benchmark |
| Not intended for | Live ad delivery, personalized causal guarantees, advertiser-wide lift or financial forecasting |
| Data | Corrected Criteo Uplift v2.1; 13,979,592 records; frozen 85/15 development/holdout |
| Outcome | Binary website visit; conversion not analyzed |
| User predictors | Exactly f0–f11 in canonical order; anonymized numeric features |
| Exclusions | Exposure, visit, conversion and row IDs; treatment excluded from user predictors |
| S intervention | Separate `__intervention_treatment` input evaluated at 0 and 1 |
| Learned policies | Treated-response, S and T LightGBM rankings; fixed random comparator |
| Frozen recipe | Binary GBDT; 200 rounds; learning rate .05; 31 leaves; minimum leaf 1000; max bin 63; two threads |
| Final fitted models | Response + control + S + six training-only nuisance models; nine files preserved unchanged |
| Nuisances | Three deterministic development-only folds; shared fold-average predictions; final-S sensitivity |
| Targeting | Top ceil(qN), q=.10/.20/.30/.40/.50; frozen random-priority/row-ID tie-breaking; none/all anchors |
| Primary recommendation | No targeting; zero hypothetical spending; not a claim of causal optimality |
| Final evaluation | Completed once using the reviewed locked workflow; closed to replay |

## Evaluation and uncertainty

The saved 765-contrast family compares fixed policies under IPW, shared DR and
final-S DR sensitivity at each assumed e=.80/.825/.85/.875/.90. The reference e=.85
is not a verified individual or experiment-specific assignment probability.
Two thousand paired Gaussian-multiplier draws produce separate pointwise and
two-sided simultaneous nominal intervals. The uncertainty is conditional on fitted
models and fixed policies. A separate treatment × visit-stratified sensitivity
conditions on observed composition; no method is chosen based on favorable results.

At reference e=.85, shared DR all-targeting minus none is 7.419 visits per 1,000
eligible, simultaneous 95% [6.376, 8.462]. All five paired shared-DR S-versus-T
intervals include zero. See [full aggregate results](../reports/portfolio/README.md)
for all fixed reaches and evaluator assumptions. Positive secondary estimates
cannot replace the primary recommendation or establish an optimal policy.

## Limitations and responsible use

Non-uniform privacy subsampling and pooled experiments with unavailable assignment
probabilities limit causal identification and population transfer. DR's robustness
property is conditional on identification and nuisance correctness; it is not a
remedy for unmeasured confounding, selection bias or dependence. Identical feature
vectors are not verified duplicate customers. No customer/experiment IDs, meaningful
dates, protected-group semantics, actual prices or revenue support fairness,
temporal drift, cluster-robust inference or profitability claims here.

The study cannot certify individualized treatment effects or acceptable targeting
fairness. Operational use would require consent/privacy, fairness and deployment
validation appropriate to a new dataset and context, plus a new prospective trial.

## Reproducibility and licensing

Source code, frozen configurations, historical aggregate reports and hash manifests
provide auditability. Private rows, models, predictions, approvals and checkpoints
are not redistributed. The presentation is reproducible from its small reviewed
aggregate snapshot; reproducing a final outcome read is neither needed nor authorized.
The [asset license](../reports/portfolio/LICENSE.md) retains Criteo attribution and
CC BY-NC-SA 4.0 restrictions, distinct from MIT-licensed software.
