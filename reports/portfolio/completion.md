# Phase 10 completion — local review only

The owner approved coordinated portfolio finalization after Stage B completed.
Work is on local branch `codex/phase-10-portfolio-finalization`, based on reviewed
commit `ac97b467bd3723c6f3ee76f3dff7c3418f30eb4f`. Nothing was pushed, opened as a
public PR, merged, uploaded or published. Owner approval of disclosure is pending.

## Deliverables

| Material | Location |
|---|---|
| Professional project overview and final recommendation | `README.md` |
| System diagram and detailed workflow | `docs/ARCHITECTURE.md`, architecture PNG/SVG |
| Portfolio case study | `docs/CASE_STUDY.md` |
| Intended use, methods and limitations | `docs/MODEL_CARD.md` |
| 30-second pitch, two-minute walkthrough, technical discussion, ten questions | `docs/INTERVIEW_GUIDE.md` |
| Phase notes and two challenging finalization questions | `INTERVIEW.md` |
| Disclosure inventory and reproduction/publication gates | `docs/PORTFOLIO_REVIEW.md` |
| Aggregate snapshot, full uncertainty table and figure guide | `reports/portfolio/` |
| Isolated presentation code and one-command renderer | `src/portfolio/`, `make portfolio` |
| Aggregate validation and rendering tests | `tests/test_portfolio.py` |
| Read-only CI definition, without data/secrets/uploads | `.github/workflows/portfolio.yml` |
| Updated completed-stage and owner review gates | `docs/PHASES.md` |

Six standalone figures are supplied as PNG and SVG: descriptive rates, policy
reach, uncertainty intervals, IPW/DR propensity sensitivity, paired S-versus-T
comparisons and architecture. Figures were visually inspected; layout validation
catches clipped labels/captions. The renderer preserves saved intervals and
produces byte-identical output in repeated runs of the same pinned runtime.

## Results presented, not rerun

- Frozen primary: no targeting; zero assignments/spending/gain relative to itself.
  The identity is not a test of advertising ineffectiveness or optimality.
- Final holdout size: 2,096,939. Observed rates: treatment 4.8543%, control 3.8202%;
  difference 1.0341 percentage points, explicitly descriptive.
- Shared DR all-targeting anchor at **assumed** e=.85: 7.419 visits per 1,000 eligible,
  pointwise 95% [6.789, 8.048], simultaneous 95% [6.376, 8.462].
- Across assumed e=.80–.90, all-targeting IPW changes +22.926 to −11.456;
  shared DR ranges 7.382–7.486. Relative stability does not verify identification.
- All ten simultaneous S-versus-T reference comparisons (IPW/shared DR × five
  reaches) include zero. No equivalence or model-optimality claim is made.
- All 765 predeclared comparisons under both IID and stratified uncertainty
  methods are retained: 1,530 aggregate rows, not selected significant findings.

Intervals retain 2,000 paired Gaussian-multiplier draws, the exact simultaneous
comparison family and conditional working-model qualifications. The presentation
does not resample or call the evaluation kernel. Costs/value remain hypothetical;
no revenue, ROI, real-world profitability or causal superiority is asserted.

## Actual verification

| Check | Actual result |
|---|---|
| `make check` | **398 passed, 20 deselected**, 134.89 seconds |
| Ruff lint | Passed |
| Ruff formatting | Passed; 105 Python files already formatted |
| Focused portfolio tests | **20 passed** |
| `make portfolio` | Six PNG/SVG figures, complete CSV and figure manifest generated |
| Aggregate provenance reconciliation | All 1,530 rows × six numeric fields match saved final results |
| Figure/table hashes | All 13 generated figure/table hashes verify |
| Stage A public lock verification | Passed without opening datasets |
| Child and recursive historical execution locks | Passed; unchanged |
| Preservation audit | 276 historical entries, 22 Phase 9 JSON artifacts and 51 campaign files unchanged |
| Dependency lockfile | Unchanged |
| `git diff --check` | Passed |
| Remote Phase 10 CI | **Not run**; no push, dispatch or public PR authorized |

The excluded tests require real full-data artifacts or historical analytical stages;
they are intentionally not a finalization reproduction command. Fast statistical,
pipeline, authorization and interruption tests use synthetic fixtures. They do
not re-execute an approved production experiment.

## Provenance and disclosure

The candidate snapshot was reconciled against the existing result manifest and
its saved aggregate files. It omits the private operational binding and exposes no
row-level records, predictions, fitted models, signatures, approvals, private backup
contents or absolute private paths. Whole-cohort support has a minimum cell count
of 12,016. This is aggregate disclosure, not a differential privacy guarantee.

Final result manifest:
`447eaa876994dbf77f141d956e80881b96892778943bb72bbcef5a7a554c0ac2`.

Presentation snapshot:
`358c331d72df76d0ca1e4fddd36c7c35be32b1a0b2dd0ae12949c5967ac46169`.

No historical locks, frozen results or private campaign state were modified. No
production operator, outcome reader, feature scorer, training run, backup or remote
write was used. All new presentation files are local candidates for owner review.

## Completion and remaining gates

- [x] All seven requested portfolio deliverables prepared locally.
- [x] Scope, disclosure, attribution and numerical provenance reviewed technically.
- [x] Local tests, lint, formatting, figure generation and preservation checks pass.
- [x] Primary recommendation preserved; no post-holdout winner selection.
- [ ] Owner approves the finished materials and exact aggregate disclosure.
- [ ] Owner separately authorizes any public push, PR, merge or publication.

The authoritative roadmap also proposes a Streamlit dashboard, deployment and a
recorded demo. Those are outside this approved finalization scope and are neither
implemented nor described as completed. Cloud filesystem persistence is not a
new cross-task guarantee; no backup operation was performed in this phase.
