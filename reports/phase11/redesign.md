# Phase 11 — Decision Intelligence UI redesign

Local review only. Branch `codex/phase-11-premium-ui` starts from the completed
Phase 11 dashboard commit `259df36e6e7c40f52c2541002cae8e149dff92e0`.
No public push, PR, merge or deployment is included.

## Design and scope

- Product: **Marketing Uplift | Decision Intelligence**; headline **Smarter Marketing
  Starts With Evidence**.
- Navy sidebar and hero, light canvas, white rounded cards, cobalt response,
  teal S-learner, violet T-learner, slate random baseline. Native accessible controls
  retain stable internal page values and widget keys.
- Executive overview leads with dataset scale and the frozen no-targeting decision;
  descriptive assignment rates, business interpretation and Predict/Evaluate/Decide
  narrative follow. The mobile KPI grid keeps the primary decision visible sooner.
- Policy performance centers the saved curve/interval chart and same-reach values,
  with no causal winner label. Sensitivity displays only the five supported scenarios;
  point-estimate ranges are descriptive display summaries, not new confidence intervals.
- Budget impact studio separates input and output surfaces; incremental value and
  spend/unspent graphics use the unchanged Decimal illustration outputs. No optimization,
  trimming, unsupported propensity or actual ROI is introduced.
- How the engine works adds a numbered end-to-end workflow, model explanations,
  paired ranking comparisons and progressively disclosed uncertainty detail.

## Actual verification

| Check | Result |
|---|---|
| Applicable full `make check` | **472 passed, 20 full-data tests deselected**, 144.63 seconds |
| Original dashboard tests | All **65 passed** unchanged |
| Focused suite including new UI regressions | **74 passed** |
| Lint / formatting | PASS; **113 Python files** |
| Minimal Python 3.12.14 / Streamlit 1.50 runtime | Five-page AppTest and actual HTTP 200 health PASS |
| Chromium page/viewport checks | All five pages at **390, 768, 1024, 1440px**; 20 checks, no app exceptions or document-width overflow |
| Screenshots | All five pages at all four widths, local review only |
| Contrast checks | Four core text/background pairs meet 4.5:1 normal-text contrast |
| Safe rendering | HTML text escaped; local CSS only; visible focus and reduced-motion support |
| Numerical preservation | Snapshot, financial module and loader byte-identical to original Phase 11 |
| Dependency preservation | `app/requirements.txt`, root `uv.lock` and `pyproject.toml` byte-identical |

Focused UI tests verify KPI values, focus-reach cards against exact saved estimates,
budget incremental-value outputs, unchanged primary recommendation, chart point/interval
preservation, allocation arithmetic, supported style choices and safe HTML escaping.
The existing numerical, provenance, interaction and private-read sentinel tests remain
unchanged. The final label-wrapping polish was followed by focused tests and another
browser/smoke pass. Browser checks and palette tests are not a formal WCAG certification.
No additional frontend dependencies, external fonts or services were introduced.

## Preservation and disclosure audit

Approved snapshot SHA-256 remains:
`358c331d72df76d0ca1e4fddd36c7c35be32b1a0b2dd0ae12949c5967ac46169`.

All historical results, figures, execution locks, fitted models and memberships are
untouched. Preservation checks use public committed files; no private artifacts,
raw records, predictions, outcomes, models or campaign checkpoints were opened.
No analytical run, final evaluation, scoring, fitting or financial optimization occurred.
No targeting remains the primary recommendation. Positive secondary diagnostics or
illustrative net values do not establish optimality, causal superiority or profitability.
Five assumed propensities and the original 765-family simultaneous uncertainty
qualification remain visible. No intervals or statistical results were recomputed.

Software remains MIT; Criteo-derived aggregates and visualizations retain Criteo AI
Lab attribution and CC BY-NC-SA 4.0 restrictions. The review ZIP contains only an
explicit public-source allowlist, the already approved public aggregate snapshot,
screenshots, diffs and verification materials. No credential, signature, row-level
array, private Git history or execution state is included. The standalone preview
folder is a convenience copy, not a new experiment or independent source of results.

## Review and remaining gates

The ZIP includes the exact changed files, a diff against the original Phase 11,
a cumulative diff against the Phase 10 merged base, screenshots, hash inventory,
verification logs and a self-contained `preview/` folder. See `docs/DASHBOARD.md`
for Mac launch instructions. The existing private GitHub review-transfer workflow
can transfer the archive after explicit authorization; this phase makes no remote writes.

- [x] Implement requested redesign without changing data or arithmetic.
- [x] Preserve 65 original tests and add focused presentation checks.
- [x] Verify five pages, four widths, minimal runtime and local health.
- [x] Prepare an independently checksummed review bundle and Mac preview steps.
- [ ] Owner personally reviews the redesigned interface.
- [ ] Owner separately approves any private transfer, public push/PR or deployment.
