# Marketing Uplift & Causal Decision Engine

**An offline advertising decision study that can recommend spending nothing.**

An advertiser wants incremental website visits, not just a list of people likely
to visit anyway. This project connects data validation, response and uplift models,
policy evaluation, uncertainty and a budget-constrained abstention rule on the
corrected **13.98 million-record Criteo Uplift v2.1 benchmark**.

**Final recommendation: retain the frozen no-targeting policy.** Positive secondary
targeting diagnostics do not establish an optimal strategy or authorize replacing
the recommendation after seeing the final holdout. Zero gain relative to no
targeting is an identity—not proof that advertising is ineffective or abstention optimal.

> Phase 9's one-time evaluation is completed and closed. These materials present
> frozen aggregate results without rerunning the evaluation or reselecting a policy.
> This is an offline portfolio study, not a deployed advertising system.

[Case study](docs/CASE_STUDY.md) · [Interview guide](docs/INTERVIEW_GUIDE.md) ·
[Model card](docs/MODEL_CARD.md) · [Architecture](docs/ARCHITECTURE.md) ·
[Aggregate results and figure guide](reports/portfolio/README.md)

[Local completion and verification evidence](reports/portfolio/completion.md)

## Interactive dashboard

Phase 11 adds an aggregate-only Streamlit dashboard: business overview, fixed-reach
comparisons, saved IPW/DR sensitivity, hypothetical budget arithmetic and paired
model explanations. The frozen primary decision stays **no targeting**. Controls
never train, score, reopen outcomes, interpolate propensity scenarios or select a new policy.

For a minimal Python 3.12 environment, from the repository root:

```sh
uv venv --python 3.12 .venv-dashboard
uv pip sync --python .venv-dashboard/bin/python app/requirements.txt
.venv-dashboard/bin/python -m streamlit run app/streamlit_app.py --server.address=127.0.0.1
```

Open `http://localhost:8501`. In an existing research development environment,
`make dashboard` launches the same app. The minimal deployment installs only the
37 pinned Streamlit runtime dependencies; it needs no models, data download,
credentials or historical analytical environment.

The budget page scales saved benchmark rates using hypothetical population,
assignment cost and visit value. It is **not validated ROI, deployment guidance or
a new causal estimate**. Scaled saved intervals do not cover transport uncertainty.

[Local launch and Community Cloud checklist](docs/DASHBOARD.md).
This branch prepares the application locally; no public deployment or live-demo
link is claimed. Publication and deployment require separate owner approval.

![End-to-end architecture](reports/portfolio/figures/architecture.png)

## What was built

| Layer | Implementation |
|---|---|
| Data engineering | Pinned revision and SHA-256; full-file contract; DuckDB/Parquet; preserved source-row mapping |
| Experimental design | Sealed 15% holdout; five frozen development re-splits; leakage and artifact-integrity tests |
| Machine learning | LightGBM treated-response, S-learner and T-learner; reproducible random targeting; MLflow provenance |
| Evaluation | Equal-reach policies at 10–50%; none/all anchors; IPW, shared DR and nuisance sensitivity |
| Decision support | Hypothetical budgets/costs/visit values; conservative marginal-benefit rule allowed to abstain |
| Final evaluation | Development-only refits; locked policies; independent prediction-backup restore; signed gates and one-time journal |
| Presentation | Aggregate-only reproducible figures, uncertainty tables, case study and model card |

## Data and leakage prevention

[Criteo's corrected release](https://huggingface.co/datasets/criteo/criteo-uplift)
contains 13,979,592 rows, 12 anonymized numeric features (`f0`–`f11`) and four binary
indicators: `treatment`, `visit`, `conversion`, `exposure`. **Visit** is the outcome;
conversion is outside this study. Exactly `f0`–`f11` are user predictors. The S-learner
receives treatment separately as an intervention indicator, not an exported user feature.
Exposure is post-assignment and never enters predictors.

The archive is exactly 311,422,618 bytes at revision
`82811785048bb633de2d55c02bab4e57066e6423`; verified SHA-256:

```text
2716e1bf0fd157a93b5bf86924d9088419dfbac2022c6cd90030220634f616dc
```

Validation and ingestion preserve all rows: no silent dropping, deduplication or
imputation. Source-row ordinals establish alignment, not customer identity.
The frozen development pool contains **11,882,653 records**; the final holdout
contains **2,096,939**. Joint treatment × visit stratification was predeclared.
Five overlapping 80/20 development re-splits assess stability; they are not five
independent experiments. The [data audit](reports/data_audit.md) documents repeated
feature vectors, concentrated distributions and covariate balance.

## Models and evaluation

The treated-response model estimates visit probability among assigned records.
The S-learner scores `p(visit | X, T=1) − p(visit | X, T=0)` using one model; the
T-learner subtracts separate arm-model predictions. An individual causal response
is never observed. All model recipes were frozen before final evaluation, with
200 LightGBM rounds, 31 leaves, learning rate 0.05 and two training threads.
Training-only nuisance folds supply the shared DR evaluator; no holdout outcome
influenced training, rankings, reach, spending or model selection.

For policy π, the target is visit value `V(π)` and incremental gain
`Δ(π) = V(π) − V(no targeting)`. Estimates below are **visits per 1,000 eligible
records**, not per targeted user. Assignment effects differ from effects of actual
exposure: no exposure conditioning or treatment-on-the-treated claims are made.

**Constant propensity e=0.85 is a reference assumption, not a verified assignment
probability.** IPW and DR are reported separately across e=0.80, 0.825, 0.85, 0.875
and 0.90. Causal interpretation additionally requires consistency, positivity,
exchangeability, no interference and suitable propensity/outcome-model correctness
in the released population. Unknown experiment IDs, varying assignment probabilities
and non-uniform privacy subsampling may violate those conditions. DR does not
automatically remove those limitations.

## Measured final results

Observed holdout rates are **4.8543% treatment** (86,523 / 1,782,398) and
**3.8202% control** (12,016 / 314,541): a **descriptive 1.0341 percentage-point
difference**, not an unqualified causal effect.

![Fixed-reach policy diagnostics](reports/portfolio/figures/policy_reach.png)

At assumed e=0.85, shared-DR secondary diagnostics are:

| Reach | Random | Treated response | S-learner | T-learner |
|---|---:|---:|---:|---:|
| 10% | 0.774 | 5.040 | 6.002 | 5.812 |
| 20% | 1.524 | 6.677 | 6.690 | 6.629 |
| 30% | 2.264 | 7.037 | 6.958 | 6.759 |
| 40% | 3.138 | 7.160 | 7.010 | 6.846 |
| 50% | 3.805 | 7.241 | 7.104 | 6.924 |

These point estimates are assumption-dependent diagnostics, not a leaderboard for
choosing the final policy. The all-targeting DR anchor is **7.419** visits per
1,000 eligible, with nominal pointwise 95% interval **[6.789, 8.048]** and
simultaneous interval **[6.376, 8.462]**. All-targeting has a different budget from
fixed-reach targeting. No-targeting has exactly zero incremental gain relative to itself.

![Propensity and nuisance sensitivity](reports/portfolio/figures/propensity_sensitivity.png)

The all-targeting IPW estimate changes from **22.926** at assumed e=0.80 to
**−11.456** at e=0.90. Shared DR ranges **7.382–7.486**, with final-S DR reported
as a separate nuisance sensitivity. Relative stability of one evaluator does not
verify its models or identification assumptions.

![Paired S-versus-T diagnostics](reports/portfolio/figures/s_vs_t.png)

All ten simultaneous S-versus-T intervals at reference e=0.85 (five reaches ×
IPW/shared DR) contain zero. This statement uses **paired contrasts**, not overlap
between two separate model intervals. No winner is reselected.

Uncertainty uses **2,000 paired Gaussian-multiplier draws** and the predeclared
**765-contrast simultaneous family**. Pointwise intervals are separate. Both are
nominal working-model intervals conditional on fitted models and fixed policies,
not exact randomization intervals or ordinary row-bootstrap intervals. The mandatory
treatment × visit-stratified sensitivity conditions on observed stratum counts;
it does not replace the primary IID working model. Full intervals for every policy,
propensity and nuisance scenario are in the [aggregate figure guide](reports/portfolio/README.md).

## Why retain no targeting?

The development decision engine abstained in **all 40 scenario/split combinations**.
Depending on the scenario, reasons included assumption sensitivity, negative
estimated net benefit, zero visit value and insufficient budget for the first
predeclared reach. Phase 9 locked that recommendation before holdout outcomes.

Positive final diagnostics answer a narrower question under stated assumptions.
They neither establish optimality across policies/costs nor justify undoing that
lock. Costs, budgets and visit values are hypothetical; **no real revenue, ROI,
cost savings or advertiser-wide causal improvement was measured**.

## Reproduce the presentation safely

Use Python 3.11/3.12 and [uv 0.12.23](https://github.com/astral-sh/uv/releases/tag/0.12.23):

```sh
uv sync --locked
make portfolio
uv run --locked pytest tests/test_portfolio.py -q
make check
```

`make portfolio` reads only the checksum-pinned aggregate snapshot. It does not
download data, load models, train, rescore, resample or execute Stage B. Six figures
are emitted as PNG/SVG plus a complete aggregate CSV and figure hash manifest.
[Reproduction and disclosure notes](docs/PORTFOLIO_REVIEW.md) explain exactly what
is reproducible without private artifacts. **Do not rerun the final evaluation.**

Historical pipeline commands and protocols remain available in the source and
[phase checklist](docs/PHASES.md); they are not a portfolio reproduction recipe.
The existing one-time journal is completed. Fresh Cloud tasks must not assume
datasets, fitted models or private checkpoints persist.

## Scope, rights and next evidence

This work demonstrates reproducible data science, tabular modeling, off-policy
evaluation and honest decision reporting. It does not validate individual causal
effects, longitudinal stability, customer-level independence or production deployment.
A future study would need experiment-specific assignment probabilities, sampling
information, dependence identifiers and real economics. A new policy would require
fresh prospective evidence, not another look at this holdout.

The Phase 10 case study describes its original static portfolio scope. Phase 11
adds the dashboard described above; no live deployment or recorded demo is claimed.
See the [case study](docs/CASE_STUDY.md) for scientific findings and limitations.

**Attribution:** Criteo AI Lab; Diemert, Betlei, Renaudin and Amini (2018),
*A Large Scale Benchmark for Uplift Modeling*, AdKDD & TargetAd.
[Official dataset notes](https://ailab.criteo.com/criteo-uplift-prediction-dataset/) ·
[Pinned source](https://huggingface.co/datasets/criteo/criteo-uplift/tree/82811785048bb633de2d55c02bab4e57066e6423).
Software retains the repository MIT license; dataset-derived portfolio assets retain
[CC BY-NC-SA 4.0 attribution and restrictions](reports/portfolio/LICENSE.md).
