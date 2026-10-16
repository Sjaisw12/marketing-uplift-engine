# Phase 5 — development descriptive assignment contrast completion

Implementation and local checks are complete; review/merge approval and Phase 6
approval remain pending. The branch is `codex/phase-5-development-ate`, based on
merged main commit `c55301e45a5cf95ccb13891f0f06d54f0aadb3be`. The finalized
nine-page roadmap, AGENTS.md, phase checklist and completed Phase 4 audit informed
this scope. Phase 4's completion approval is now checked in docs/PHASES.md.

## Actual development results

| Quantity | Observed |
|---|---:|
| Total frozen development records | 11,882,653 |
| Treatment records / visits | 10,100,257 / 490,301 |
| Control records / visits | 1,782,396 / 68,089 |
| Treatment visit probability | 0.048543418251634586 |
| Control visit probability | 0.03820082630347016 |
| Absolute descriptive contrast | 0.010342591948164427 |
| Nominal 95% working-model interval | [0.010030712098551624, 0.010652817315469083] |
| Difference in percentage points | 1.0342591948164428 |
| Nominal interval in percentage points | [1.0030712098551624, 1.0652817315469083] |
| Visit outcomes per 1,000 assignments | 10.342591948164428 |
| Nominal per-1,000 interval | [10.030712098551625, 10.652817315469083] |

Counts were aggregated through the verified frozen development boundary and
reconciled exactly with Phase 4. The whole development pool was used once;
the five overlapping development repetitions were not pooled. Percentage points
are absolute probability differences ×100, not relative percentage changes.

## Statistical interpretation

The reported point is an **unadjusted descriptive assignment contrast**. Causal
ITT interpretation requires additional assumptions about assignment exchangeability,
selection, consistency and interference. Non-uniform privacy subsampling and
pooled experiments with unknown assignment probabilities can bias this contrast.
The observed overall treatment fraction does not establish a common propensity.

The predeclared 95% Newcombe–Wilson hybrid score interval uses no continuity
correction. It is a **nominal working-model interval**, not exact randomization-based
inference or a correction for the treatment × visit stratified development selection.
Row/arm independence are working assumptions; missing entity/experiment IDs
prevent justified cluster correction. Repeated feature vectors do not identify
valid clusters. A zero-excluding interval does not address these sources of bias.

There was no exposure filtering, conditioning or adjustment, treatment-on-the-treated
estimation, model fitting, individual uplift, policy optimization, financial claim,
or final holdout outcome analysis.

## Independent numerical evidence

Fourteen fixed cases include equal/unequal sample sizes, zero/all-event arms,
one-record extremes, positive/negative contrasts and actual development counts.
They were generated independently with Statsmodels **0.14.5**
`statsmodels.stats.proportion.confint_proportions_2indep`, using `method='newcomb'`,
`compare='diff'`, `alpha=0.05`, `correction=False`. Inspection confirmed that this
branch combines uncorrected Wilson score bounds. Statsmodels and its import
dependency Patsy **1.0.2** were installed only under an isolated `/tmp` target;
no dependency or lockfile changes were needed.

Every endpoint also agreed to absolute tolerance **1e-12** with independent
**70-digit Decimal score-quadratic roots** using a high-precision normal quantile.
The committed fixture records expected binary64/high-precision values, arguments,
version, reference source hash and tolerance. The generator imports no project
estimator; CI tests use the offline fixture, not an optional library install.

Production numerical operations use SciPy **1.16.2** `special.ndtri(0.975)`, binary64
Wilson bounds, `math.sqrt` and `math.hypot`. Full formulas and references appear in
`reports/development_ate.md`. No interval method was chosen after viewing results.

## Actual checks and preservation

- `make ate` completed on all existing frozen development records.
- `make check`: **99 fast tests passed**; Ruff lint and formatting passed.
- Read-only integration selection:
  `pytest tests/test_full_data.py tests/test_data_audit_full.py tests/test_development_ate_full.py -m full_data -k 'not reconstruct' -q`:
  **8 passed, 1 deselected**. It rechecks original source identity and complete
  Parquet row mapping, preserved Phase 4 evidence, actual development counts,
  independent interval references, all membership integrity and aggregate scales.
  The original reconstruction test was excluded to avoid unnecessarily rewriting
  its protected verification report.
- New tests include 14 independent reference examples, count validation, known
  zero/all-event Wilson roots, arm-swap symmetry, absolute-unit scaling, synthetic
  development-only count checks, repeatability, exposure/conversion invariance,
  Phase 4 reconciliation failure, missing-membership refusal and changed-input refusal.
- All **22 protected data and Phase 3/4 provenance files** stayed byte-identical,
  including the archive, Parquet, frozen registry, all **12 memberships**, acquisition
  manifest, validation/ingestion/reconstruction evidence and Phase 4 reports.
- No data were reacquired, ingested, deduplicated, imputed, reconstructed or resplit.
  The sealed holdout was accessed only through membership-integrity checks.

The existing one-thread, 2 GB DuckDB memory and 6 GB spill limits remain unchanged.
Only row IDs, treatment and visit are projected for analysis. Outputs are aggregate
Markdown/JSON; raw data, Parquet and memberships remain Git-ignored. Existing data
and evidence are not rewritten. No new storage-persistence guarantee is implied.

## Review artifacts and CI

Review `src/marketing_uplift/development_ate.py`, the reference generator/fixture,
statistical and read-only integration tests, CLI routing, documentation and the
machine-readable/human-readable development reports. Manual GitHub Actions now
runs `make ate` after Phase 3/4 verification, tests the results and preservation,
and uploads only small reports. No remote Phase 5 full-data execution is claimed
by this local report. Phase 6 remains unimplemented and gated. Do not merge this
change or begin Phase 6 before the user approves.
