# Phase 10 release readiness

Status: **conditionally approved for publication preparation** following independent
scientific, numerical, visual and disclosure review. This is not authorization for
public aggregate disclosure or any push, PR, merge or publication.

## Scope and identities

This follow-up changes documentation only. Public-facing wording describes the
completed study without announcing an approval state. Operational approval gates
remain explicit in this review record and the phase checklist.

- Independently reviewed Phase 10 commit: `49c43c95c9b6b8de621e0af67ec97423afa8a1c0`.
- Proposed PR base: last verified merged main, `ac97b467bd3723c6f3ee76f3dff7c3418f30eb4f`.
- No remote refresh was performed; the file list is exact against that local base.
- Aggregate snapshot SHA-256:
  `358c331d72df76d0ca1e4fddd36c7c35be32b1a0b2dd0ae12949c5967ac46169`.
- Original final result-manifest SHA-256:
  `447eaa876994dbf77f141d956e80881b96892778943bb72bbcef5a7a554c0ac2`.
- Preserved child execution lock:
  `b7dca1de6089f2f621c4972d078c906f126205d837e8485064633a326f9e212c`.

The aggregate snapshot, original verification JSON, figure/table bytes, figure
manifest and rendering code retain their reviewed identities. Historical
`local-review-only` JSON fields are provenance, not a mutable release authorization.
No scientific estimate, interval, model recipe, policy or execution code is changed.

## Proposed public-disclosure summary

| Material | Technical review result |
|---|---|
| Whole-cohort counts | Four aggregate treatment/visit cells; smallest cell 12,016; no feature/subgroup or record-level exports |
| Policy results | All 765 predeclared contrasts under both uncertainty methods; 1,530 aggregate rows retained |
| Units and assumptions | Visits per 1,000 eligible; e=.85 explicitly assumed, with .80–.90 sensitivity |
| Uncertainty | Nominal conditional working-model intervals; pointwise versus 765-family simultaneous coverage distinguished |
| Primary recommendation | No targeting remains frozen; zero relative gain is an identity, not ineffectiveness or optimality evidence |
| Secondary diagnostics | Positive estimates do not select a final policy; paired S/T findings do not establish equivalence or superiority |
| Restricted artifacts | No raw rows, IDs, memberships, fitted models, prediction/nuisance arrays, checkpoints, private MLflow or GitHub artifacts |
| Secrets and approvals | No actual credentials, private keys, signatures or signed authorization envelopes; test denylist literals are not secrets |
| Financial/deployment claims | No realized revenue, ROI, cost saving, causal superiority or deployed dashboard claim |
| Provenance | Snapshot and every saved figure/table hash preserved; complete CSV reconciles with snapshot |
| Rights | Software remains MIT; Criteo-derived assets retain attribution and CC BY-NC-SA 4.0 restrictions |
| Publication permission | **Separate explicit owner approval remains required**, including disclosure of these aggregates |

Pattern scans and small aggregate cells do not establish differential privacy or
prove absence of every possible disclosure risk. The accepted review concerns this
specific portfolio evidence; it does not validate benchmark causal identification.
The Git diff also contains removed historical preparation statements, which must
not be mistaken for current scientific or execution claims.

## Applicable local validation

| Check | Actual result |
|---|---|
| `make check` | PASS: 398 passed, 20 full-data tests deselected; 132.32 seconds |
| Ruff lint / formatting | PASS; 105 Python files already formatted |
| Portfolio tests | All 20 pass within the full applicable suite |
| Public Stage A lock validator | PASS; datasets not opened |
| Child and parent locks / nine frozen models | PASS; byte identities unchanged |
| Aggregate snapshot / figure provenance | PASS; reviewed snapshot, all figures/table and manifest unchanged |
| Aggregate CSV | All 1,530 rows reconcile with the pinned snapshot |
| Protected historical/private artifacts | PASS; 276 historical entries, 22 Phase 9 JSON artifacts and 51 campaign files unchanged |
| Public-disclosure scan | PASS; all 34 proposed files and diff checked; no restricted artifacts or credential-pattern matches |
| Documentation links / whitespace | PASS |

Full-data tests, production experiments and Stage B are outside this task. Tests
use bounded synthetic fixtures or saved aggregates; no real model training, scoring
or outcome access is performed. Original figures were not regenerated or rewritten.

Remote CI is not run because no push or PR is authorized. The original Phase 10
verification JSON is preserved as historical evidence, rather than rewritten.

## Exact proposed PR file list

The list below is the complete change set against the local base above, including
this release-readiness document. It is a proposal only, not a public disclosure.

```text
.github/workflows/portfolio.yml
INTERVIEW.md
Makefile
README.md
docs/ARCHITECTURE.md
docs/CASE_STUDY.md
docs/INTERVIEW_GUIDE.md
docs/MODEL_CARD.md
docs/PHASES.md
docs/PORTFOLIO_REVIEW.md
docs/RELEASE_READINESS.md
reports/portfolio/LICENSE.md
reports/portfolio/README.md
reports/portfolio/aggregate_results.json
reports/portfolio/completion.md
reports/portfolio/figures/architecture.png
reports/portfolio/figures/architecture.svg
reports/portfolio/figures/descriptive_rates.png
reports/portfolio/figures/descriptive_rates.svg
reports/portfolio/figures/diagnostic_comparisons.csv
reports/portfolio/figures/figure_manifest.json
reports/portfolio/figures/policy_reach.png
reports/portfolio/figures/policy_reach.svg
reports/portfolio/figures/propensity_sensitivity.png
reports/portfolio/figures/propensity_sensitivity.svg
reports/portfolio/figures/s_vs_t.png
reports/portfolio/figures/s_vs_t.svg
reports/portfolio/figures/uncertainty_intervals.png
reports/portfolio/figures/uncertainty_intervals.svg
reports/portfolio/verification.json
src/portfolio/__init__.py
src/portfolio/__main__.py
src/portfolio/presentation.py
tests/test_portfolio.py
```

Canonical file-list identity: SHA-256 of the UTF-8 sorted paths above, one path per
line with a final newline:
`77b1270b4b1dd8f609ee7d621e99283a6107c13b3abddc89023d4ceae366be81`.

## Final owner gates

- [x] Independent scientific, numerical, visual and disclosure review passed.
- [x] Conditional approval covers local release preparation only.
- [x] Public-facing approval-state wording made publication-neutral.
- [x] MIT software and CC BY-NC-SA 4.0 dataset-derived rights remain distinct.
- [ ] Owner explicitly approves the exact aggregate disclosure and final PR file list.
- [ ] Owner separately authorizes the public push/PR operation.
- [ ] Owner separately authorizes merge or other publication, if desired.
