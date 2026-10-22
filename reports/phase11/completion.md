# Phase 11 — aggregate dashboard and deployment readiness

Completed locally on `codex/phase-11-aggregate-dashboard`, based on merged main
`7a038ffe4e0902b37aa287c125fd6ae87941cbf5`. No push, PR, merge, deployment or live
demo URL is included. Owner review and separate publication/deployment approval remain.

## Delivered

- Five-page Streamlit app: overview, equal-reach comparisons, saved sensitivity,
  hypothetical budget illustration, and paired model/limitations explanations.
- Fixed public snapshot loader with the existing checksum/schema validator; no
  model, raw-data, outcome, membership, checkpoint or credential interfaces.
- Saved IPW/shared-DR rows at exactly five assumed propensities. Both saved
  pointwise and 765-family simultaneous intervals, with primary IID and separately
  labeled stratified sensitivity. No new CI, interpolation, bootstrap or evaluation.
- Budget cap, eligible population, assignment cost and incremental-visit value
  inputs. Exact ceil reach counts and Decimal budget checks; no automatic trimming,
  winner selection or change to the primary policy. Negative results are retained.
- Responsive native controls, tables and Vega-Lite charts, high-contrast theme,
  minimal toolbar, provenance, contextual caveats and licensing attribution.
- Minimal pinned 37-package Python 3.12 deployment closure, entrypoint, safe local
  launch targets, headless smoke script and future CI definition.
- Local launch, provider deployment and post-verification demo-link instructions
  in `docs/DASHBOARD.md`; Phase 11 checklist and interview explanations updated.

## Scientific boundaries

No targeting remains the frozen primary recommendation. Zero assignments/spend
and gain relative to itself are identities, not proof that advertising is ineffective
or abstention optimal. Controls explore secondary diagnostics only. Assumed e=.85
and sensitivity .80/.825/.85/.875/.90 are not verified assignment probabilities or
a calibrated distribution. Privacy subsampling, pooled experiments, unknown assignment
and possible dependence continue to limit identification. DR does not erase them.

The simulator scales an approved gain per 1,000 **eligible** records by hypothetical
N/1000; it does not multiply by targeted count. Scaled interval endpoints are the
same benchmark bounds under deterministic scaling—not new-population confidence
intervals. Price/value and transfer assumptions are unvalidated. No real ROI,
advertiser-wide causal improvement, model equivalence or deployment advice is claimed.

## Actual local verification

| Check | Result |
|---|---|
| Full applicable `make check` | **463 passed, 20 full-data tests deselected**, 127.50 seconds |
| Focused dashboard tests after final UI changes | **65 passed** |
| Ruff lint / format | PASS; 111 Python files formatted consistently |
| Minimal runtime install | Exactly 37 pinned packages installed successfully in a separate Python 3.12.14 environment |
| Minimal runtime dependency check | PASS; all installed requirements compatible |
| Minimal environment AppTest | All five pages execute without exceptions |
| Real headless server | HTTP 200 / `ok`; loopback only; smoke server terminated afterward |
| Research-package isolation | No LightGBM, DuckDB, MLflow or Matplotlib installed in the minimal runtime |
| Chromium browser review | Desktop 1440×1000; mobile 390×844; no mobile document overflow (390px content / 390px viewport) |
| Private-read sentinel / import restrictions | PASS across all pages and interactive tests |
| Public historical preservation | 153 tracked historical files byte-identical to base; recursive execution lock verifies |
| Raw/private artifact handling | No private model/data/checkpoint/credential files opened; no campaign operation |
| Remote CI / Community Cloud | **Not executed or deployed**; readiness only |

Dashboard tests cover provenance failure, saved evaluator/scenario/interval
selection, unsupported input rejection, descriptive rates, eligible-population
scaling, negative results, zero cost/value, ceil rounding, exact budget rejection,
paired sign reversal, chart points and bounds, empty displays, dependency closure,
all five pages, uncertainty changes and private-read/import sentinels. Existing
schema/family validation tests remain unchanged and pass in the full suite.

An initial server launch was blocked by the Codex shell sandbox's socket permission.
The same app started with loopback networking permitted; no app recipe, data,
environment setting or public binding was substituted to hide the failure. Streamlit
AppTest's bare-mode ScriptRunContext warning is expected; no app exception occurred.

Browser checks inspect representative pages and a mobile viewport, not every
device or a formal WCAG audit. Final text/axis-label polish and the minimal toolbar
were followed by the focused tests and minimal-environment smoke again.

## Preserved provenance and release boundaries

The approved aggregate SHA-256 remains
`358c331d72df76d0ca1e4fddd36c7c35be32b1a0b2dd0ae12949c5967ac46169`.
The original execution child lock remains
`b7dca1de6089f2f621c4972d078c906f126205d837e8485064633a326f9e212c`.
The original result manifest remains
`447eaa876994dbf77f141d956e80881b96892778943bb72bbcef5a7a554c0ac2`.

All prior report/figure bytes, rendering code, analytical code, configurations,
dependency lockfile and frozen membership registry remain unchanged. Verification
compared committed public files and lock metadata only; it did not reopen private
artifacts or claim fresh verification of private dataset/model bytes. No protected
state was written. Existing private assets remain outside the app's access paths.

Software remains MIT; Criteo-derived aggregates/visualizations retain Criteo AI Lab
attribution and CC BY-NC-SA 4.0 restrictions. No private artifacts or credentials
are introduced into the candidate source or deployment configuration.

- [x] Implement requested scope and pass local verification.
- [x] Document exact entrypoint and minimal dependency/provider configuration.
- [x] Preserve the frozen scientific and operational boundaries.
- [ ] Owner reviews app, scientific wording and deployment instructions.
- [ ] Owner separately approves push/PR/merge of Phase 11.
- [ ] Owner separately approves and verifies public Community Cloud deployment.
- [ ] Add a real live-demo link only after that verification and approval.
