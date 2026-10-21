# Marketing Uplift | The Decision Lab

A separate, static, editorial web experience for a newcomer to marketing uplift.
React + TypeScript + Vite; no backend, model server, account, analytics, secrets or
research execution. The existing Streamlit application is untouched.

The story moves from a hypothetical customer example, through the real benchmark
and saved policy comparisons, into an illustrative budget lab and the frozen
no-targeting decision. Technical readers can expand the identification, paired
uncertainty and provenance explanations. No scientific experiment runs in the browser.

## Preview the review package on a Mac

Extract into a **new** directory. Do not overwrite previous project copies.
The review package includes a prebuilt `site/dist/` folder. From `site/`:

```bash
python3 -m http.server 8000 --bind 127.0.0.1 --directory dist
```

Open **http://localhost:8000**. If Python is available through existing uv instead:

```bash
uv run --no-project --python 3.12 python -m http.server 8000 --bind 127.0.0.1 --directory dist
```

Use HTTP localhost, not a double-clicked `file://` URL: fetch and Web Crypto need
a supported browser context. This does not install research dependencies or access
any source records. Stop the server with Control-C. Use a different free port if needed.

## Work from source

Use **Node.js 24 LTS** and npm (tested Node 24.19.0 / npm 11.9.0). If Node 24 is
not installed on the Mac, the prebuilt preview above avoids requiring it for review.

```bash
cd web
npm ci
npm run dev
```

Open the printed localhost address (normally http://127.0.0.1:5173).

```bash
npm run check
npm test
npm run format:check
npm run build
npm run preview
```

`npm ci` uses the committed npm lockfile. React, React DOM and decimal.js are the
only production dependencies; charts and explanatory illustrations are local SVG.
Vite, strict TypeScript, Vitest, jsdom, Testing Library and Prettier are development
tooling. Development-only files and fixtures are not shipped in `dist/`.

## Data boundary

The **only** runtime fetch is the same-origin `aggregate_results.json`. Raw bytes
are SHA-256 checked before JSON parsing, then the schema, count reconciliation,
primary policy, methodology and all 1,530 comparison rows are validated. Build
verification independently checks the same hash and rejects unexpected public assets.

```
358c331d72df76d0ca1e4fddd36c7c35be32b1a0b2dd0ae12949c5967ac46169
```

`public/aggregate_results.json` is byte-identical to the approved Phase 10 snapshot.
Its historical `local-review-only` metadata is preserved; public aggregate disclosure
was separately approved in Phase 10. This site's publication still needs approval.
Never edit, regenerate or silently replace it. The UI has no upload, URL input,
private-path selector or experiment fallback. Validation failure stops the experience.

No targeting is the frozen primary policy. Alternatives are secondary diagnostics.
The budget lab uses 28-significant-digit, half-even decimal arithmetic and exact
integer ceiling reach counts, matching the verified Python illustration semantics
for supported numeric UI inputs. It never multiplies gain by targeted count, trims
an unaffordable policy or clips negatives. Financial display preserves large decimal
values without converting them to imprecise JavaScript Numbers. Scaled saved bounds
are not new-population confidence or prediction intervals.

The 200 Python-derived fixtures cover all four diagnostic rankings, five reaches,
two evaluators and five propensity scenarios at fixed illustrative inputs. They
are public-aggregate arithmetic checks, not new estimates. No Python runtime or
fixture is needed by the deployed website.

## Local review materials

- `CONTENT_MAP.md`: scientific numbers, exact aggregate fields and interface locations.
- `VISITOR_REVIEW.md`: newcomer-understanding checklist and review limits.
- `DEPLOYMENT.md`: static hosting proposal, privacy boundaries and owner gates.
- `VERIFICATION.md`: actual test, production-build and browser evidence.
- `NOTICE.md` and `LICENSE`: Criteo-derived CC BY-NC-SA 4.0 versus MIT software.

Screenshots, the source diff, file inventory and validation logs are in the private
review package alongside `site/`. This work neither pushes nor deploys anything.

## Final scientific and launch-quality review

`FINAL_REVIEW.md` contains the current finishing-pass results (2,111 frontend tests,
expanded Python references, browser/a11y checks and honest remaining gates).
`NEWCOMER_TEST.md` is the independent-human acceptance script. Creator attribution
and safe sharing settings are in `site.config.json`. Production URL is deliberately
unset; `npm run release:check` must block publication readiness until an exact
owner-reviewed HTTPS root and rebuilt social metadata are available.

Original `VERIFICATION.md` remains the historical initial-build report. The current
review package includes 35 new browser captures, the 1200×630 social preview,
numerical/disclosure evidence and a source diff. It is prepared locally only.

## Current scientific narrative reconciliation

The follow-up explanation-only pass identifies the original e=.90 IPW binding
condition, the IPW/DR augmentation identity and the nine qualified higher-reach
contrasts. See [scientific reconciliation](../docs/SCIENTIFIC_RECONCILIATION.md).
The earlier FINAL_REVIEW.md is a historical quality-gate report; current scientific
narrative and public launch remain **BLOCKED pending owner review** and the
separate human/host/publication gates. Frozen aggregates and arithmetic are unchanged.
