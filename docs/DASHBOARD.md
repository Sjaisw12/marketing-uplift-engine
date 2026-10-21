# Aggregate dashboard: launch and deployment readiness

Phase 11 is local implementation and review only. No public push, PR, merge,
deployment, new experiment or holdout access is included. Base merged main:
`7a038ffe4e0902b37aa287c125fd6ae87941cbf5`.

## What the app does

| Page | Interaction and boundary |
|---|---|
| Overview | Dataset/development/holdout counts, descriptive arm rates and frozen no-targeting primary policy |
| Policy comparisons | Four rankings at fixed 10/20/30/40/50% reach; saved intervals; none/all anchors separated |
| Sensitivity explorer | IPW and shared DR across exactly .80/.825/.85/.875/.90; points/whiskers without interpolation |
| Budget illustration | Hypothetical eligible population, cost, visit value and budget cap; no automatic policy selection |
| Models & limitations | Paired saved policy differences, learner definitions, conditional uncertainty and identification caveats |

All pages retain the primary recommendation. Explorer choices are secondary
diagnostics, not a new final policy. No decision-engine rule is rerun. The app
uses no raw records, outcome files, memberships, models, credentials or private state.

## Source and provenance

The only runtime source file is `reports/portfolio/aggregate_results.json`, checked
on every app rerun against SHA-256
`358c331d72df76d0ca1e4fddd36c7c35be32b1a0b2dd0ae12949c5967ac46169`.
The existing Phase 10 allowlist validator checks the full family, schema, finite
values, saved interval conventions and primary-policy identity. Missing or changed
data stops the interface without fallback. There are no uploads, custom file paths,
remote data fetches, model imports or execution controls.

The app selects saved IPW/shared-DR rows; it does not generate an interval or
recalculate a statistic from individual observations. The simultaneous intervals
still cover the original **765-contrast** family, including comparisons and nuisance
sensitivity not displayed by a particular app filter. Filtering does not shrink
that family or create new coverage. Pointwise intervals are distinct. Both are
nominal working-model uncertainty conditional on fitted models and fixed policies,
using the completed 2,000 paired Gaussian-multiplier draws. They are not ordinary
row-bootstrap or exact randomization intervals.

Fixed-stratum uncertainty is a separately labeled sensitivity conditioning on
observed treatment × visit composition. It does not replace primary IID uncertainty;
zero conditional variance is not causal certainty. No cross-method joint coverage
or independent-replication claim for overlapping development splits is made.

## Budget arithmetic and limits

For hypothetical population N, nominal saved reach q, cost c and visit value v:

```text
assignments = ceil(q × N)
estimated incremental visits = N × saved_gain_per_1000 / 1000
hypothetical spending = assignments × c
hypothetical net benefit = v × estimated incremental visits − spending
```

Decimal arithmetic enforces the budget cap before reporting a candidate. An
unaffordable candidate fails; it is not trimmed, interpolated or silently replaced.
None always gives zero assignments/spend/gain, with no statistical CI for that
identity. Negative gain/net value is retained. Zero cost/value is allowed.

Population scaling assumes benchmark gain rates transfer unchanged. This is an
**assumption-dependent illustration, not validated ROI, deployment guidance or a
new causal estimate**. Saved benchmark endpoints are multiplied by N/1000; these
are scaled bounds, not confidence or prediction intervals for a new population.
No uncertainty about transport, prices or value is inferred. At small N,
ceil-rounding changes actual reach; benchmark rates remain those at nominal q.
The UI makes that rounding explicit. No actual people can be selected by this app.

## Local launch (recommended minimal environment)

From the repository root, with Python 3.12 and uv installed:

```sh
uv venv --python 3.12 .venv-dashboard
uv pip sync --python .venv-dashboard/bin/python app/requirements.txt
uv pip check --python .venv-dashboard/bin/python
.venv-dashboard/bin/python -m streamlit run app/streamlit_app.py --server.address=127.0.0.1
```

Open `http://localhost:8501`. Do not overwrite an existing environment without
reviewing it; a new environment name is fine. The example directory is Git-ignored.
An already configured research workspace can instead use `make dashboard`.

The entrypoint is **`app/streamlit_app.py`**. It adds only the fixed repository root
and `src` paths needed for trusted aggregate-validation imports. `.streamlit/config.toml`
sets a high-contrast light theme and minimal toolbar, disables usage telemetry/file
watching, and retains CORS/XSRF protections. Local commands bind loopback only.
After editing code, restart the server (Ctrl-C, same launch
command); no runtime file watcher scans analytical assets.

Native Streamlit controls have visible labels/help, keyboard interaction and mobile
sidebar behavior; metrics/columns and Vega-Lite charts adapt to the viewport. Chart
legends, tooltips and numerical tables supplement color. This is not a formal WCAG
certification or a claim of tested behavior on every browser/device.

## Local verification

```sh
uv run --locked pytest tests/test_dashboard.py -q
make check
.venv-dashboard/bin/python tests/smoke_dashboard.py
```

The smoke script uses only the minimal deployment environment: it executes all five
pages with Streamlit AppTest and starts a real loopback server, checks HTTP health,
then terminates it. It does not need pytest in that environment. The full suite
excludes production/full-data stages; statistical/execution checks use synthetic
fixtures or saved aggregates. No live historical stage is executed.

The new `dashboard.yml` CI definition repeats minimal Python 3.12 dependency and
headless checks after a future approved push. It does not deploy, use secrets,
download data or upload artifacts. No remote CI run is claimed for this local phase.

## Streamlit Community Cloud deployment — owner action after approval

The [official dependency documentation](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies)
specifies entrypoint-directory precedence. `app/requirements.txt` is deliberately
beside the entrypoint, so Community Cloud uses it before the historical root
`uv.lock`/research environment. The app's 37-package Python 3.12/Linux runtime closure
is pinned to the locally verified versions; it includes no LightGBM, DuckDB,
scikit-learn, MLflow or Matplotlib. No apt packages or secrets are required.
The original dependency lockfile and all historical execution locks remain unchanged.

1. Review this branch, scientific language and tests. Separately authorize a push/PR
   and its eventual merge. No such action is performed now.
2. After approval, ensure the published target branch contains this app, its
   dependency file, `src/portfolio/` and the approved aggregate snapshot.
3. Sign in to Streamlit Community Cloud with the owner's GitHub account and choose
   **Create app**. Use repository `Sjaisw12/marketing-uplift-engine`, the approved
   published branch (normally `main` after review), and `app/streamlit_app.py`.
4. In **Advanced settings**, explicitly select **Python 3.12**. Leave secrets empty;
   do not provide project signing keys, Git credentials or private storage access.
5. Only with separate public-deployment approval, choose **Deploy**. Verify build
   logs use `app/requirements.txt` and do not install the research stack.
6. Open the app in a signed-out/private browser window. Confirm all five pages,
   mobile layout, all five saved propensities, uncertainty labels, primary no-targeting
   decision, budget rejection, provenance and license attribution. Inspect logs for
   exceptions. Community Cloud deployment itself remains **unverified until this step**.
7. Confirm intended public visibility, copy the actual app URL and review it. Check
   cold starts, resource limits and service terms in the owner's account; no paid
   service or availability guarantee is assumed by this repository.
8. Only after approval and a successful live check, add the real URL as a **Live
   aggregate demo** link in README and the GitHub About website field. Do not invent
   a URL or mark deployment complete before verification.

See the [official deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app).
Provider UI and supported runtimes can change; recheck the linked official pages
at the time of deployment rather than silently changing dependency recipes.

## Attribution and release scope

Criteo AI Lab; Diemert et al. (2018), *A Large Scale Benchmark for Uplift Modeling*.
Criteo-derived aggregates and benchmark visualizations retain **CC BY-NC-SA 4.0**;
app/software code retains the repository **MIT** license. No Criteo endorsement,
real advertiser-wide causal impact, realized financial benefit or deployment
recommendation is implied. The one-time final evaluation remains closed.

## Decision Intelligence redesign (local review)

The UI-redesign branch starts from the complete Phase 11 dashboard, not main.
The product is **Marketing Uplift | Decision Intelligence**, with five display names:
Executive overview, Policy performance, Sensitivity & robustness, Budget impact
studio, and How the engine works. Original internal navigation values and widget
keys remain stable for compatibility. The entrypoint and dependency pins are unchanged.

The presentation system in `app/design.py` uses a navy navigation rail, light
canvas, white cards, cobalt response, teal S-learner, violet T-learner and slate
random-policy identities. Styling uses local scoped CSS and native keyboard-operable
Streamlit controls, with no external fonts, asset service or frontend framework.
Cards and diagrams become grids at narrower widths. There is no public deployment.

The overview explains the frozen no-targeting decision before deeper analysis.
Same-reach cards display exact saved estimates; the sensitivity panels summarize
only the displayed saved point-estimate ranges. These ranges are descriptive
summaries, not additional uncertainty intervals or statistical tests. The simulator
adds a hypothetical incremental-value tile and spend/unspent graphic using the
unchanged Decimal illustration outputs. No new statistical quantity is estimated.

For a standalone review ZIP, open a new directory and verify its checksum before
extracting. The `preview/` directory contains only the app, unchanged public
snapshot/loader, licensing and deployment documentation. From that directory:

```bash
uv venv --python 3.12 .venv-dashboard
uv pip sync --python .venv-dashboard/bin/python app/requirements.txt
.venv-dashboard/bin/python -m streamlit run app/streamlit_app.py --server.address=127.0.0.1
```

Open `http://localhost:8501`. No dataset download, model loading, GitHub credentials,
checkpoint restore or execution approval is needed. Keep the directory separate
from previous project copies. Close another local app using port 8501 first, or
add `--server.port=8502`. Screenshots, file hashes, diffs, test evidence and the
redesign audit are provided separately in the review ZIP. A private review transfer
can be requested; no upload or public release is implied by packaging.
