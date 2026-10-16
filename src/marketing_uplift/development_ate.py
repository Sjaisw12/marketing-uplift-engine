"""Descriptive development assignment contrast with a nominal working-model interval."""

import json
import math
from numbers import Integral
from pathlib import Path

import duckdb
import scipy
from scipy.special import ndtri

from marketing_uplift.data_audit import protected_snapshot
from marketing_uplift.data_contract import ContractError, atomic_json, connection, identity, now
from marketing_uplift.features import development_relation
from marketing_uplift.ingestion import file_sha256

ATE_JSON = Path("reports/development_ate.json")
ATE_MD = Path("reports/development_ate.md")
REFERENCE_FILE = Path(__file__).resolve().parents[2] / "tests/fixtures/newcombe_wilson_95.json"
CONFIDENCE = 0.95
Z = float(ndtri(0.975))


def valid_counts(events, size):
    if (
        isinstance(events, bool)
        or isinstance(size, bool)
        or not isinstance(events, Integral)
        or not isinstance(size, Integral)
        or size <= 0
        or not 0 <= events <= size
    ):
        raise ContractError("Counts require integer n>0 and integer 0<=visits<=n")
    return int(events), int(size)


def wilson(events, size):
    """95% Wilson score limits without continuity correction, in binary64."""
    events, size = valid_counts(events, size)
    p = events / size
    denominator = 1 + Z * Z / size
    center = (p + Z * Z / (2 * size)) / denominator
    radius = Z / denominator * math.sqrt(p * (1 - p) / size + Z * Z / (4 * size * size))
    # Physical bounds remove only floating-point excursions; negative contrasts remain valid.
    return max(0.0, center - radius), min(1.0, center + radius)


def assignment_contrast(treatment_visits, treatment_n, control_visits, control_n):
    x1, n1 = valid_counts(treatment_visits, treatment_n)
    x0, n0 = valid_counts(control_visits, control_n)
    p1, p0 = x1 / n1, x0 / n0
    l1, u1 = wilson(x1, n1)
    l0, u0 = wilson(x0, n0)
    difference = p1 - p0
    lower = max(-1.0, difference - math.hypot(p1 - l1, u0 - p0))
    upper = min(1.0, difference + math.hypot(u1 - p1, p0 - l0))
    return {
        "treatment": {
            "records": n1,
            "visits": x1,
            "visit_probability": p1,
            "visit_percent": 100 * p1,
        },
        "control": {
            "records": n0,
            "visits": x0,
            "visit_probability": p0,
            "visit_percent": 100 * p0,
        },
        "difference_probability": difference,
        "interval_probability": [lower, upper],
        "difference_percentage_points": 100 * difference,
        "interval_percentage_points": [100 * lower, 100 * upper],
        "difference_per_1000_assignments": 1000 * difference,
        "interval_per_1000_assignments": [1000 * lower, 1000 * upper],
        "arm_wilson_intervals": {"treatment": [l1, u1], "control": [l0, u0]},
    }


def analysis_snapshot(config):
    protected = protected_snapshot(config)
    for name in (
        "reports/data_audit.json",
        "reports/data_audit.md",
        "reports/phase_4_data_audit.md",
    ):
        path = Path(name)
        if path.exists():
            protected[name] = {"bytes": path.stat().st_size, "sha256": file_sha256(path)}
    return protected


def analyze_development(config):
    before = analysis_snapshot(config)
    source = Path(config["data"]["raw_directory"]) / config["data"]["filename"]
    if before[source.as_posix()] != {
        "bytes": config["data"]["size_bytes"],
        "sha256": config["data"]["sha256"],
    }:
        raise ContractError("Raw source identity changed; refusing analysis")
    registry_path = Path(config["experiment"]["split_registry"])
    registry = json.loads(registry_path.read_text())
    audit_path = Path("reports/data_audit.json")
    audited = json.loads(audit_path.read_text())
    if (
        audited["status"] != "passed"
        or audited["source"] != identity(config)
        or audited["registry_sha256"] != file_sha256(registry_path)
        or audited["development_membership_sha256"]
        != registry["memberships"]["development"]["sha256"]
    ):
        raise ContractError("Phase 4 evidence does not match the frozen development source")
    try:
        with connection(config) as con:
            # Project only IDs, assignment and visit after the verified membership boundary.
            development_relation(con, config).project("row_id,treatment,visit").create_view(
                "ate_development"
            )
            counts = con.execute("""SELECT treatment,count(*),sum(visit::BIGINT),
                count(DISTINCT row_id),
                count(*) FILTER (WHERE visit IS NULL OR visit NOT IN (0,1))
                FROM ate_development GROUP BY treatment ORDER BY treatment""").fetchall()
    except duckdb.Error as error:
        raise ContractError(f"Development contrast stopped: {type(error).__name__}") from None
    if len(counts) != 2 or {r[0] for r in counts} != {0, 1}:
        raise ContractError("Exactly two nonempty assignment arms are required")
    arms = {t: (n, visits) for t, n, visits, _, _ in counts}
    if any(unique != n or invalid for _, n, _, unique, invalid in counts):
        raise ContractError("Development identifier uniqueness or binary visit contract failed")
    n0, x0 = arms[0]
    n1, x1 = arms[1]
    total = n0 + n1
    if (
        total != registry["memberships"]["development"]["rows"]
        or total != audited["development_rows"]
    ):
        raise ContractError("Analysis count differs from frozen development size")
    observed_strata = {"T0_V0": n0 - x0, "T0_V1": x0, "T1_V0": n1 - x1, "T1_V1": x1}
    if observed_strata != audited["strata"]["development"]:
        raise ContractError("Development counts disagree with the completed Phase 4 audit")
    result = {
        "analysis_version": 1,
        "status": "passed",
        "created_at_utc": now(),
        "scope": "all frozen development records once; no repeated-split pooling",
        "estimand_label": "unadjusted descriptive assignment contrast",
        "outcome": "visit",
        "assignment": "treatment",
        "development_rows": total,
        "source": identity(config),
        "registry_sha256": file_sha256(registry_path),
        "development_membership_sha256": registry["memberships"]["development"]["sha256"],
        "phase4_audit_sha256": file_sha256(audit_path),
        "observed_strata": observed_strata,
        "statistics": assignment_contrast(x1, n1, x0, n0),
        "interval_method": {
            "name": "Newcombe-Wilson hybrid score, method 10; no continuity correction",
            "confidence_level": CONFIDENCE,
            "z_975": Z,
            "interpretation": "nominal working-model interval; not exact randomization inference",
            "numerics": (
                "binary64 Wilson score bounds, scipy.special.ndtri, math.sqrt and math.hypot"
            ),
            "formula": "d=p1-p0; lower=d-hypot(p1-L1,U0-p0); upper=d+hypot(U1-p1,p0-L0)",
            "reference": (
                "Statsmodels 0.14.5 confint_proportions_2indep(method='newcomb', "
                "compare='diff', alpha=0.05, correction=False)"
            ),
            "reference_fixture_sha256": file_sha256(REFERENCE_FILE),
            "reference_check": (
                "14 frozen cases also checked using independent 70-digit Decimal "
                "score-quadratic roots"
            ),
        },
        "assumptions_and_limitations": [
            (
                "Independent Bernoulli observations within arms and independent arms are "
                "working assumptions, not verified design facts."
            ),
            (
                "Development selection was stratified on treatment x visit; the interval is"
                " not an exact split- or randomization-based interval."
            ),
            (
                "ITT interpretation requires consistency, no interference, exchangeable "
                "assignment and suitable selection assumptions in the released sample."
            ),
            (
                "Non-uniform privacy subsampling and unknown pooled experiment-specific "
                "assignment probabilities can bias the contrast."
            ),
            (
                "An overall treatment fraction near 0.85 does not prove a common "
                "propensity; no propensity weighting or causal correction is applied."
            ),
            (
                "Missing user and experiment IDs prevent justified entity/experiment "
                "cluster correction; repeated vectors do not identify clusters."
            ),
            (
                "The interval excludes neither selection bias nor unobserved heterogeneity "
                "and does not quantify advertiser-wide or production impact."
            ),
        ],
        "exposure_conditioned_on": False,
        "treatment_on_treated_estimated": False,
        "holdout_outcomes_analyzed": False,
        "models_or_individual_uplift_computed": False,
        "duckdb_version": duckdb.__version__,
        "scipy_version": scipy.__version__,
        "resources": config["resources"],
    }
    if analysis_snapshot(config) != before:
        raise ContractError("Protected inputs changed; refusing to publish analysis")
    result["protected_artifacts"] = before
    result["protected_artifacts_unchanged"] = True
    markdown = render_markdown(result)
    atomic_json(ATE_JSON, result)
    # Report outputs only. This does not alter any protected source/provenance artifact.
    import os
    import tempfile

    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=ATE_MD.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(markdown)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(ATE_MD)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return result


def render_markdown(report):
    s = report["statistics"]
    low, high = s["interval_probability"]
    low_pp, high_pp = s["interval_percentage_points"]
    low_1000, high_1000 = s["interval_per_1000_assignments"]
    t, c = s["treatment"], s["control"]
    arm_rows = "\n".join(
        "| "
        + " | ".join(
            [
                label,
                f"{arm['records']:,}",
                f"{arm['visits']:,}",
                f"{arm['visit_probability']:.12f}",
                f"{arm['visit_percent']:.8f}%",
            ]
        )
        + " |"
        for label, arm in [("Treatment", t), ("Control", c)]
    )
    scale_rows = "\n".join(
        [
            f"| Probability difference | {s['difference_probability']:.12f} | "
            f"[{low:.12f}, {high:.12f}] |",
            f"| Percentage points | {s['difference_percentage_points']:.8f} | "
            f"[{low_pp:.8f}, {high_pp:.8f}] |",
            "| Visit outcomes per 1,000 assignments | "
            f"{s['difference_per_1000_assignments']:.8f} | "
            f"[{low_1000:.8f}, {high_1000:.8f}] |",
        ]
    )
    return f"""# Development assignment contrast — Phase 5

This is an **unadjusted descriptive treatment/control visit-rate contrast** across
{report["development_rows"]:,} frozen development records. Its interpretation as a
causal intention-to-treat (ITT) effect requires additional assumptions. The final
holdout was not analyzed, and no models, individual uplift or policies were fitted.

## Observed counts and probabilities

| Assignment | Records | Visit outcomes | Visit probability | Visit percentage |
|---|---:|---:|---:|---:|
{arm_rows}

| Scale | Treatment minus control | Nominal 95% working-model interval |
|---|---:|---:|
{scale_rows}

A percentage-point difference is 100 times the probability difference. It is **not**
a relative percentage change, which would instead be 100×(p_T/p_C−1). No relative
percentage-change claim is reported. Per-1,000 values are 1,000 times the absolute
probability difference; the corresponding interval is scaled identically.

Numerically, the descriptive contrast corresponds to
**{s["difference_per_1000_assignments"]:.6f} more visit outcomes per 1,000 assignments**
in the observed treatment/control comparison. Interpreting this as incremental
visits caused by assigning 1,000 otherwise comparable records to advertising rather
than control requires the causal assumptions below. It is not a claim about actual
ad exposures, impressions, total repeated visit volume, revenue, ROI or campaign savings.

## Predeclared interval and independent numerical verification

The interval is the **95% Newcombe–Wilson hybrid score interval (method 10), without
continuity correction**. Let p_i=x_i/n_i, z=Phi^(-1)(0.975), and d=p_1−p_0. For each arm:

```text
D_i = 1 + z²/n_i
C_i = (p_i + z²/(2 n_i)) / D_i
R_i = z sqrt(p_i(1−p_i)/n_i + z²/(4 n_i²)) / D_i
L_i = C_i − R_i; U_i = C_i + R_i
lower = d − sqrt((p_1−L_1)² + (U_0−p_0)²)
upper = d + sqrt((U_1−p_1)² + (p_0−L_0)²)
```

Calculations use binary64 arithmetic, SciPy {report["scipy_version"]}
`scipy.special.ndtri(0.975)` (z={report["interval_method"]["z_975"]:.17g}), `math.sqrt`
and `math.hypot`. Only numerical excursions outside physical probability bounds
are clipped; negative contrasts and interval endpoints remain valid. This method
handles unequal arm sizes and avoids degenerate Wald intervals at zero/all events.

Fourteen frozen reference cases, including zero/all events, one-record arms,
unequal sizes, positive/negative contrasts and the actual development counts,
were established using **Statsmodels 0.14.5**
`confint_proportions_2indep(method="newcomb", compare="diff", alpha=0.05, correction=False)`.
That branch uses Wilson limits and has no continuity correction. Every reference
also agrees within 1e-12 with independent 70-digit Decimal calculations that solve
the score quadratic rather than use the project's Wilson implementation.

Reference fixture SHA-256: `{report["interval_method"]["reference_fixture_sha256"]}`.
`tests/fixtures/newcombe_wilson_95.json` stores inputs, expected endpoints, the
reference function's source hash, high-precision endpoints and library metadata.
`scripts/generate_newcombe_references.py` reproduces the external check; Statsmodels
and Patsy were installed only in an isolated temporary reference directory and are
not project dependencies. Offline tests use the committed values.

Method references: Newcombe (1998), *Interval estimation for the difference between
independent proportions: comparison of eleven methods*, Statistics in Medicine;
[Statsmodels reference documentation](https://www.statsmodels.org/v0.14.5/generated/statsmodels.stats.proportion.confint_proportions_2indep.html).

## Interpretation and statistical limitations

- This is a **nominal working-model interval**, not an exact randomization-based
  confidence interval. Independent Bernoulli records within arms and independent
  arms are assumptions. Under these assumptions it addresses sampling variability,
  not uncertainty in the arithmetic of the fixed observed development contrast.
- Development was selected by joint treatment × visit stratification. Outcome
  counts are constrained by that selection. The interval is not exact conditional
  inference for this selection procedure and is not uncertainty generated by split
  seeds. The five overlapping development repetitions are not five independent
  experiments and are not pooled to multiply the sample size.
- A causal ITT interpretation requires consistent assignment/outcome definitions,
  no interference, exchangeable assignment in the analyzed population, and suitable
  selection assumptions. Criteo's non-uniform privacy subsampling can undermine
  those assumptions and alter the released-sample contrast.
- Pooling experiments with unknown assignment probabilities can mix different
  baseline risks and treatment probabilities. Hidden experiment/advertiser IDs
  prevent stratified adjustment. A marginal treated fraction near 0.85 does not
  prove a common propensity, and no assumed-propensity correction is applied here.
- Missing entity/experiment IDs prevent justified cluster correction. Phase 4's
  repeated feature vectors do not prove common users or supply valid cluster IDs.
  The nominal interval may understate uncertainty if records are dependent.
- A narrow or zero-excluding interval does not resolve selection bias, pooled
  confounding, interference, unknown sampling weights or advertiser-wide validity.
- Exposure is post-assignment. No exposure filtering, adjustment, conditioning,
  division by exposure rates or treatment-on-the-treated estimation was performed.
  Conversion remains outside the V1 visit analysis.
- No conclusions about advertiser-wide effects, production behavior, measured
  financial returns, temporal stability or optimal targeting are supported.

## Reproducibility and preservation

Only `row_id`, `treatment` and `visit` are projected through the verified development
membership boundary. Aggregate counts reconcile exactly with the completed Phase 4
audit. The complete development pool is used once; no splits or datasets are regenerated.

Source SHA-256: `{report["source"]["sha256"]}`.
Frozen registry SHA-256: `{report["registry_sha256"]}`.
Development membership SHA-256: `{report["development_membership_sha256"]}`.
Phase 4 audit SHA-256: `{report["phase4_audit_sha256"]}`.
All {len(report["protected_artifacts"])} existing protected data and Phase 3/4 provenance files,
including every frozen membership and the sealed holdout, retained identical sizes
and hashes before/after analysis. Holdout IDs are used only for integrity checks;
no holdout outcome summaries are requested.

Run `make ate` with the existing verified Phase 3/4 artifacts. The command uses the
existing one-thread, 2 GB DuckDB query-memory and 6 GB spill limits and publishes
only aggregate Markdown/JSON. Raw records, Parquet and membership arrays stay
outside Git. Phase 6 modeling and final holdout evaluation remain gated.
"""
