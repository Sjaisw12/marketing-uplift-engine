# Decision Lab — final local quality gate

Scope: one finishing pass on the existing cream/forest/terracotta React experience.
Base: `0ed2ce5db88805d30c72543263f2bf2ca92c6383`.
Branch: `codex/decision-lab-release-quality`. No push, PR, merge or deployment.
This report supplements the historical `VERIFICATION.md`; its earlier results
remain historical evidence, not the current test count.

## Changes and scientific clarifications

- Replaced the research heading with “The ad-assigned group had a higher observed
  visit rate.” Exact group denominators, observed rates and percentage-point
  difference remain descriptive, with assignment distinguished from exposure.
- Added a selected-policy example beside the plot: at 20% reach, 1,000 eligible
  records imply 200 assignments; the saved S-learner reference estimate is 6.690
  additional visits **per all 1,000 eligible records**, not per 200 ads. The example
  follows the selected reach, ranking and saved scenario. It is neither a conversion
  percentage nor an individual effect, guaranteed benefit or new-audience forecast.
- Separated historical Criteo assignments, evaluated hypothetical policies and the
  site's absence of live advertising. Retained zero future assignments as the
  frozen primary recommendation, never as evidence of global optimality.
- Explained why the predeclared conservative, sequential spending framework could
  abstain despite positive secondary diagnostics. Checked all 40 published Phase 8
  scenario/split decisions: all abstained. These are not independent replications.
  The decision framework's uncertainty gate is distinct from the final diagnostic
  765-comparison family; neither was recalculated or altered.
- Added explicit conceptual advertising OFF/ON instructions, short chapter
  takeaways and a business-use explanation that limits external generalization.
- Preserved layout/navigation/hero/teaching graphic/plots/dark-green decision reveal.
  Added coherent green keyboard focus, mobile legibility improvements, complete
  chart descriptions, a keyboard-scrollable exact-values table and valid ARIA.
- Credited **Sanyam Jaiswal** with the owner-provided GitHub URL. Added repository,
  case-study, model-card and technical-documentation links; no LinkedIn placeholder
  or invented professional title. Stack and engineering scope are expandable.
- Added original 1200×630 social artwork, reviewed metadata configuration, static
  distribution auditing and a mechanical URL prerequisite check. No production
  hostname was invented; `productionUrl` remains `null`.

## Actual verification

| Gate | Observed result |
|---|---|
| Vitest | **2,111 passed**, four files |
| Independent Python references | **840** selected estimates/intervals, **200** direct paired T-minus-S comparisons and **804** exact Decimal illustrations; all matched |
| Existing Python dashboard regression | **78 passed**; Streamlit source untouched |
| TypeScript / Prettier / new Python Ruff lint and format | PASS |
| Production build | PASS; JS 305.26 kB / gzip 98.23 kB; CSS 31.38 kB / gzip 7.24 kB |
| Distribution disclosure check | PASS: seven files, 1,110,231 bytes; exact snapshot, asset allowlist, no source maps or credential-format matches |
| Clean locked installation | Offline `npm ci`, build and all 2,111 tests passed in a separate directory; seven distribution files byte-identical |
| Production dependency audit | Zero reported vulnerabilities at verification time, not a security guarantee |
| Static browser navigation | 24 chapter/viewport checks at 390, 768, 1024 and 1440 px; no horizontal document overflow or header-covered chapter anchors |
| Deep links / refresh | All six anchors at desktop and mobile: 12 direct loads and 12 refreshes passed |
| Browser history / keyboard focus | Back/forward, visible keyboard focus, selected-vs-focus styling passed |
| Console / loading | No captured runtime exceptions, console errors or failed resource requests; loaded resources same-origin |
| Accessibility | axe-core 4.14.0: zero reported violations in four desktop/mobile collapsed/expanded scans, WCAG 2 A/AA, 2.1 A/AA and best-practice tags |
| Screenshots | 35 actual Chromium captures, including six chapters at four widths, explanatory plot/unit sections, author credit and keyboard focus |
| Internal links | Every fragment resolves |
| External links | Six public HEAD requests returned 200; Creative Commons connection blocked by environment proxy: `Tunnel connection failed: 403 Forbidden` |
| Metadata | Local title, description, author, OG title/type/site name and favicon checked; social PNG dimensions verified; synthetic Pages-subpath absolute metadata tested |
| Launch prerequisite | **Intentionally BLOCKED**: `npm run release:check` exits 2 because production URL is unset |

The original 200 Python budget fixtures also continue to pass. New reference
coverage spans both selectable evaluators, five saved propensities, both saved
uncertainty models and both saved interval types. It includes all four rankings at
five reaches, the all-targeting anchor, negative/budget-failure cases, ceiling
assignments and large Decimal inputs. The no-targeting output remains an identity.
The schema checks all 1,530 saved rows, including the unselectable nuisance
sensitivity evaluator; filtering the UI never shrinks the frozen comparison family.
These are public-snapshot/arithmetic checks, **not new statistical estimation**.

## Provenance and disclosure boundary

The approved snapshot remains byte-identical in source and distribution:
`358c331d72df76d0ca1e4fddd36c7c35be32b1a0b2dd0ae12949c5967ac46169`.
The loader, financial helper, original figures/results, experiment locks, memberships,
models, root dependency lock and campaign state were not modified. No private
artifacts were opened. The only research material read was already-public aggregate
JSON and the already-published Phase 8 report. No outcome access, scoring, training,
backup operation or experiment occurred.

The static artifact contains HTML, bundled JS/CSS, approved public aggregates,
favicon and original social artwork. No model, row-level data, prediction array,
checkpoint, signature, execution interface, analytics or third-party font is shipped.
Allowlisting plus credential-format scanning reduces accidental disclosure; it is
not proof against arbitrary future source changes. Owner review remains required.
MIT covers application software; Criteo-derived aggregates and visualizations retain
CC BY-NC-SA 4.0 attribution, noncommercial and share-alike conditions. See `NOTICE.md`.

## Remaining human and live checks — not claimed complete

- Run `NEWCOMER_TEST.md` with an actual independent person. No external-user test
  or comprehension result is claimed.
- Test Mac Safari, VoiceOver, zoom/text scaling and a physical small-screen device.
  Chromium emulation is not equivalent to those checks or WCAG certification.
- axe leaves SVG/text contrast items for manual determination because of graphic
  overlap/image backgrounds. Core CSS contrast tests and visual review passed;
  assistive-technology and full manual accessibility review remain outstanding.
- Verify the Creative Commons destination from the Mac; the environment denied the
  proxy tunnel, so this check cannot establish either availability or a broken link.
- Choose and review the exact HTTPS production root, configure `site.config.json`,
  review the configuration-bound tests, rebuild, rerun `release:check` and approve
  the exact artifact before any publication. Local metadata intentionally omits
  canonical/absolute image URLs while the hostname is unknown.
- Only after separately authorized deployment: verify real HTTPS/subpath/cache
  behavior, absolute image reachability and LinkedIn Post Inspector rendering.
  Local artwork and synthetic URL tests do not establish crawler compatibility.
- Obtain explicit owner authorization before source push, public PR or hosting.

Local finishing pass: PASS. **Public launch: not cleared** until the separate
owner, hostname, human-review and live-host gates above are satisfied.
