# PR #16 — final reviewer follow-up and pre-launch review

Scope: presentation/documentation/test corrections and read-only feasibility only.
No alternative analysis, model fit, feature scoring, Stage B call or final-holdout
record access was performed. No Vercel configuration, merge or deployment occurred.

## Synchronization and preserved upstream work

Fast-forwarded the existing branch from `42120bb` to remote commit
`1de1c493c21a06b50d6331dc310c0ebf3530e23e` before editing. Preserved all four new
commits (`16c3054`, `730e21c`, `90d3bfa`, `1de1c49`): React CI, the frozen-rule
headline, simplified technical copy, removal of visible hashes/ceremonial wording,
and matching tests. No force push, reset or new PR is used.

## Exact changes

- `web/src/App.tsx`: preserves “The frozen rule said no spend. Here's why.”,
  all 40/5/5/30/120 facts, first 10% tranche and e=.90 binding condition. Explains
  assumed 90% assignment and changed weights in everyday language without calling
  the stress test invalid. Shortens the visible IPW/DR note; retains exact values,
  equations and limitations in closed technical details. Removes redundant
  process-oriented phrases; no layout, color, controls or computations changed.
- `web/tests/reconciliation.test.tsx`: two additional checks for the first-read
  explanation, preserved headline, technical disclosure and absence of visible hashes.
- `README.md`: three-sentence introduction, an existing local website screenshot,
  concise rule finding, Python/LightGBM/MLflow/React/TypeScript/Vite stack, explicit
  Codex assistance acknowledgement, React versus local Streamlit distinction,
  PR/methodology links and a non-link location for a later verified Vercel URL.
- `docs/DEVELOPMENT_EXPLORATION_FEASIBILITY.md`: unexecuted proposals for reduced
  propensity-family and normalized-IPW development analysis, inputs/uncertainty,
  role preservation, leakage controls and post-hoc interpretation limits.
- `docs/ARM_BALANCE_FEASIBILITY.md`: unexecuted predicted-risk arm means and exact
  augmentation decomposition plan; no visit query is required for that diagnostic.
- `web/DEPLOYMENT.md`: concrete future Vercel settings, hostname/metadata procedure,
  deployment-trigger warning and verification sequence; no infrastructure change.
- `web/README.md`: points to this current review and its unexecuted proposals.
- `tests/test_prelaunch_documentation.py`: three new documentation-boundary tests.
- `INTERVIEW.md`: reviewer follow-up explanation and two hard methodological questions.
- `docs/images/decision-lab-overview.png`: existing approved local hero screenshot,
  reused without regenerating the website or inventing a deployed screenshot.
- `docs/images/decision-lab-decision-desktop.png`, `decision-lab-decision-mobile.png`,
  `decision-lab-explanation-desktop.png`, `decision-lab-explanation-mobile.png`:
  new local Chromium screenshots of the current decision chapter.
- `docs/PRELAUNCH_REVIEW.md`: this completion/review report.

## Scientific evidence and unchanged boundaries

Original `reports/phase_8_metrics.json` records all 40 abstentions, with five explicit
zero-value gates, five infeasible initial reaches and 120 candidate ranking stops
in the other 30 configurations. All bind at unnormalized IPW, assumed e=.90, in the
first 10% tranche. Saved support exceeded the event threshold. Fixed-policy
A/e−B/(1−e) decreases mechanically with e; this does not invalidate the prespecified
stress objective or establish universal advertising ineffectiveness/optimal abstention.

The same 2,096,939-record denominator, IPW 10.341310853, shared DR 7.419188765 and
−2.922122088 augmentation remain available in the technical detail. The nine saved
higher-reach response/S/T simultaneous contrasts still include zero; no superiority,
equivalence or new policy is claimed. Financial arithmetic, all saved values,
intervals, 765-comparison family and source-data definitions are unchanged.

The approved snapshot remains byte-identical:
`358c331d72df76d0ca1e4fddd36c7c35be32b1a0b2dd0ae12949c5967ac46169`.
No frozen report, estimator, decision logic, dependency lock, model manifest or
historical execution lock was edited. Private campaign state and final-holdout
predictions/outcomes were never opened. The read-only inventory hashed development
artifacts only; it calculated no new prediction means, alternative gains or decisions.

## Feasibility findings — NOT experimental results

65 development files and five validation membership payload hashes verified for
all original seeds. Existing role labels and saved predictions can be reused;
no split regeneration is needed. Removing e=.90 would require a predeclared
240-coordinate one-sided family, or explicitly conservative reuse of old 300-family
bounds; saved joint points/covariance/draws are available for a separately approved
aggregate-only computation. A Hájek partial-policy proposal uses whole-arm
normalization and ratio-aware covariance; its recommended standalone family has
20 marginal coordinates. Fixed constant propensities cancel within those ratios.
Neither proposal changes the final 765-family or the original recommendation.

Arm-balance diagnostics need development IDs, treatment and saved shared m0/m1,
not final outcomes, new scoring or even development visit values. Their algebraic
decomposition cannot identify hidden experiments, prove DR correct or establish
the causal bias direction of descriptive visit-rate differences. See the two
linked feasibility reports for precise formulas, inputs and approval boundaries.

## Actual local verification and screenshots

- Frontend: **2,119 tests passed**, TypeScript, Prettier, aggregate SHA verification,
  production build and seven-file static distribution audit passed.
- Targeted Python narrative/portfolio/dashboard suite: **104 tests passed**.
- Full applicable local Python lint/format/non-full-data suite: **482 passed,
  20 full-data tests deselected**; no full-data workflow was requested.
- Static Chromium at 390/768/1024/1440px: 24 chapter/viewport navigation checks,
  12 deep-link loads, 12 refreshes, history/focus and same-origin-only resource
  checks passed. No captured runtime/console errors or failed resources.
- Four axe scans (desktop/mobile, details closed/expanded): zero reported violations;
  SVG contrast/manual items are not a WCAG certification or VoiceOver test.
- 45 current local screenshots; the four decision views linked above are included
  in the PR. The modified mobile and desktop explanations were visually inspected.
- The upstream `Decision Lab frontend checks` workflow remains unchanged and will
  run its exact install, data, TypeScript, formatting, tests and build/audit steps.
  Actual GitHub results belong to the final head commit's PR Checks, not a claim
  inferred before the remote run finishes.

[Desktop decision](images/decision-lab-decision-desktop.png) ·
[Desktop explanation](images/decision-lab-explanation-desktop.png) ·
[Mobile decision](images/decision-lab-decision-mobile.png) ·
[Mobile explanation](images/decision-lab-explanation-mobile.png)

## Remaining items and readiness assessment

**8/10 pre-launch engineering/editorial assessment**, a judgment rather than a
measured probability of success. Source/CI readiness does not grant deployment
approval. Permanent causal/generalization limitations are documented, not “solved”
by a polished UI. No live deployment or outside-user comprehension study is claimed.

- **P0:** owner reviews this final copy, tests and PR; separately authorizes merge
  and hosting. Choose/review the exact HTTPS production root, update metadata in a
  reviewed presentation-only change, rebuild and pass `release:check`. Verify human
  newcomer comprehension and real Mac/Safari/VoiceOver/mobile behavior. After a
  separately approved deployment, verify HTTPS/hash/cache/anchors and social metadata
  before claiming the launch is complete or promoting it.
- **P1:** the two development-only proposals are optional research follow-ups,
  not launch prerequisites. Execute only after a separately approved exploratory
  protocol; label post-hoc findings and preserve the original recommendation.
- **P2:** optional recorded walkthrough and post-launch performance/crawler checks;
  add the real README URL only after verification. Do not invent a URL/profile.

Vercel checklist: [deployment instructions](../web/DEPLOYMENT.md). Root `web`, Node
24.x (verify account support), `npm ci`, `npm run build`, output `dist`, no research
backend/secrets. Repository import can trigger deployment: do not connect/configure
it until approved. No automatic deployment has been enabled by this work.
