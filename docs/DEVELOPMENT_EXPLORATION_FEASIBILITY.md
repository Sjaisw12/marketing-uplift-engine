# Development-only exploratory analysis — feasibility, not results

**Status: feasible in this workspace; execution NOT approved and NOT performed.**
This report proposes post-hoc development analyses after the final evaluation.
Neither proposal changes the original recommendation, selects a new final policy,
reopens the holdout or supplies confirmatory evidence. No alternative gain, interval,
recommendation or arm-balance diagnostic was calculated during this audit.

## Verified inputs and original populations

The existing workspace contains all five original development splits, seeds
104729, 130363, 155921, 181081 and 206369. Read-only byte-hash checks verified:

- 65 saved development files: per split, four Phase 6 score/S-nuisance arrays,
  three Phase 7 T-score/shared-nuisance arrays and its fit manifest, plus five
  Phase 8 role/uncertainty/recommendation/application files.
- All five sorted validation membership payload hashes, excluding `.npy` headers
  according to the original registry convention.
- Each validation population has 2,376,531 records. Original Phase 8 selection
  and assessment roles have 1,188,265 and 1,188,266 records respectively.
- The processed Parquet file exists (201,099,097 bytes). Only filesystem metadata
  was checked; its records/columns were not opened. No holdout file was opened.

Sources: `reports/phase_6_metrics.json`, `reports/phase_7_metrics.json`,
`reports/phase_8_metrics.json`, `artifacts/splits.json`, and the original
`src/marketing_uplift/decisions.py` / `decision_metrics.py`.
Private file values are not published in this report. Source manifests already
record expected byte/ID hashes and model/prediction provenance.

Reuse existing memberships and roles, rather than reconstructing them. If a role
file were missing, the original deterministic recipe is available: sorted frozen
validation positions, PCG64(split seed + 6,000,000), half assigned selection by
permutation, remaining positions assessment. Any separately approved reconstruction
must match the original role-file and selection/assessment ID hashes; it must never
regenerate the registry or substitute different memberships. This audit did not
invoke reconstruction or inspect array values.

Predictions remain those from models trained outside each outer validation split.
No final-refit/holdout prediction files are inputs. All outputs, if approved, belong
in a new explicitly exploratory namespace; never overwrite Phase 6–9 evidence.

## Proposal A — omit assumed e=.90 from a development stress test

Freeze all eight economics, original role-specific rankings/ties/ceil reaches,
support gates, models and seeds. Retain IPW, shared DR and S-nuisance DR at assumed
e=.80/.825/.85/.875. The original rule still includes .90 and remains untouched.

The saved JSON records alone are **not sufficient** to recalibrate simultaneous
uncertainty: dropping a reason code or ignoring selected rows of the original
lower bounds does not define a newly calibrated family. The verified selection/
assessment `*-uncertainty.npz` files preserve points, covariance and 2,000 shared
Gaussian draws, so this proposal can be computed from aggregate evidence without
reading development outcomes or refitting/rescoring.

The original one-sided decision family was 300 marginal coordinates:
3 evaluators × 5 propensities × 4 rankings × 5 tranches. The proposed family is
240 coordinates after removing .90 from each evaluator. Each scenario also has a
sixth residual ranking bin in the stored moment vector; it is not a decision-family
tranche. Preserve original scenario/layout mappings explicitly when selecting rows.

Recommended predeclaration, subject to approval:

1. Project the original joint draws/covariance onto the retained coordinates.
   Reuse the original Gaussian draws so comparisons stay paired; no new favorable
   seed or nuisance specification is chosen.
2. Recompute the 95th percentile of the maximum standardized one-sided deviation
   over the declared 240-coordinate family. Retain the original recorded numerical
   zero tolerance and document it; do not infer a new model from singular directions.
3. Apply the unmodified successive-tranche rule to selection evidence under this
   clearly different exploratory family. Persist exploratory choices before applying
   them to the unchanged assessment role; never invoke a production coordinator.
4. Report every split/configuration, including continued abstention, spending and
   support. Assessment is reused development data, not fresh confirmation. The five
   overlapping splits are descriptive stability checks, not independent experiments.

An alternative is to keep the original 300-coordinate critical value while ignoring
.90 in the objective. Its retained bounds remain conservative for the subset, but
it is **not** the recalibrated 240-family procedure. Choose the primary exploratory
convention before execution; do not select the more favorable result afterward.
No family change applies to the frozen final **765 two-sided diagnostic contrasts**.

Removing the binding scenario need not produce targeting; uncertainty, economics
and other scenarios can still block it. The existing records identify the original
trigger, not the result of this proposed counterfactual rule.

## Proposal B — define a normalized/Hájek partial-policy contrast

A precise candidate estimand is released-development incremental visits per
eligible record for a fixed policy pi, relative to no targeting. Define, over
**all N records in one original role**:

```
a1_i = T_i*pi_i*Y_i/e          b1_i = T_i/e
 a0_i = (1-T_i)*pi_i*Y_i/(1-e) b0_i = (1-T_i)/(1-e)
G_H(pi) = mean(a1)/mean(b1) - mean(a0)/mean(b0)
```

Use whole-arm denominators, not selected-arm denominators. This preserves per-eligible
units and gives zero for pi=0; selected-arm rate differences would require separate
reach scaling and target a different quantity. For constant e, factors cancel within
each arm, so this particular normalized IPW point functional is identical across
all five constant-e scenarios. That is a mathematical scaling property, not proof
that unknown assignment mechanisms or privacy selection no longer matter. Positivity,
exchangeability/consistency/no interference and release-population limitations remain.

For one policy let mu1=mean(a1)/mean(b1), mu0=mean(a0)/mean(b0). The delta-method
influence contribution is:

```
psi_i = (a1_i - mu1*b1_i)/mean(b1)
      - (a0_i - mu0*b0_i)/mean(b0)
Cov(mean estimates) = sample_cov(psi)/N
```

Apply the same construction to disjoint tranches. Require both arm denominators
positive; retain support gates and fixed rankings. If approved, use 2,000 paired
Gaussian multipliers over a predeclared family, distinguish pointwise from one-sided
simultaneous bounds, and keep coverage conditional on fitted models/fixed policies.
Do not count identical constant-e normalized coordinates as independent evidence.
Recommended primary proposal: one standalone normalized-IPW family of **20 marginal
coordinates** (four rankings × five tranches), using the original eight economics.
Constant-e duplicates are not repeated as independent coordinates. Compare saved
IPW/DR outputs descriptively at reference e=.85; do not claim a formal superiority
comparison from that standalone family. A mixed simultaneous family with unchanged
DR would be a separately approved extension needing all cross-covariances.

**What is recoverable:** the saved six-bin support tables contain arm/event counts,
so fixed-policy normalized point arithmetic can be reconstructed from aggregates.
The original covariance contains joint IPW event-contribution information, but has
no explicit whole-arm denominator coordinate. For IPW-only binary outcomes, one
could derive an augmented event/arm-count covariance using binary identities and
multiple IPW weight rows. Such recovery needs its own synthetic/direct-reference
tests and numerical review; merely rescaling the old IPW intervals is incorrect.
Covariances with DR denominator adjustments are not established by the current JSON
summary. A proposed simplest auditable implementation is therefore a new bounded
**development-only** pass over ID, treatment, visit and the already-saved predictions/
rankings, collecting joint numerator/denominator moments. This is new development
computation requiring separate approval, not a new training run or holdout analysis.

If the original family were replaced/expanded for an exploratory comparison, its
critical value must be recomputed for that exact family. Do not reuse the frozen
300 or 765 critical values as though they calibrated a different ratio statistic.

## Leakage, resource and interpretation controls

- Hash-check source registry, all required development artifacts and recipes first.
  Enforce IDs are subsets of the frozen development membership before any query.
- Query only explicit columns joined to the exact original role IDs; never use an
  unrestricted Parquet scan/holdout entry point or a full-source outcome summary.
- Use existing memmaps, 65,536-row batches, one DuckDB thread and the existing 2GB
  DuckDB memory / 6GB temporary-disk caps. Inventory verification is not a benchmark
  of the proposed computations; check actual available resources before approval.
- Preserve role-specific ranking reconstruction; no data-driven seeds, preprocessing,
  re-ranking convention, models, costs, thresholds or assumptions may be tuned.
- Record a separate post-hoc protocol, artifact provenance and complete results.
  The assessment roles and all development evidence have already been examined.
- Neither proposal may replace the frozen no-targeting recommendation or be presented
  as new final-holdout performance, real ROI or causally optimal deployment guidance.

No alternative recommendation is reported. Approval of this feasibility report or
of website copy is not authorization to execute either proposal.
