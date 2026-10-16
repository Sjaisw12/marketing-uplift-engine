"""Development-only descriptive audit; no causal contrasts or model fitting."""

import json
import math
import tempfile
from pathlib import Path

import duckdb
import numpy as np
import pyarrow as pa

from marketing_uplift.data_contract import (
    COLUMNS,
    FEATURES,
    ContractError,
    atomic_json,
    connection,
    identity,
    now,
    source_path,
)
from marketing_uplift.features import development_relation
from marketing_uplift.ingestion import file_sha256, parquet_path
from marketing_uplift.splits import get_member, registry_members

AUDIT_JSON = Path("reports/data_audit.json")
AUDIT_MD = Path("reports/data_audit.md")
PERCENTILES = [0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99]


def protected_snapshot(config):
    """Hash existing assets only; never acquire, ingest, reconstruct, or rewrite them."""
    registry_path = Path(config["experiment"]["split_registry"])
    registry = json.loads(registry_path.read_text())
    paths = [source_path(config), parquet_path(config), registry_path]
    paths += [Path(spec["path"]) for spec in registry_members(registry)]
    paths += [
        Path(p)
        for p in [
            config["data"]["manifest"],
            "reports/validation.json",
            "reports/ingestion.json",
            "reports/split_reconstruction.json",
        ]
        if Path(p).exists()
    ]
    return {p.as_posix(): {"bytes": p.stat().st_size, "sha256": file_sha256(p)} for p in paths}


def numeric(value):
    return float(value) if value is not None and math.isfinite(value) else None


def balance_metrics(control, treated):
    """SMD denominator is sqrt((sample variance T + sample variance C) / 2)."""
    vc, vt = control["variance"], treated["variance"]
    if vc is None or vt is None:
        return {"smd": None, "variance_ratio": None, "smd_status": "insufficient variance data"}
    pooled = math.sqrt((vc + vt) / 2)
    delta = treated["mean"] - control["mean"]
    smd = delta / pooled if pooled > 0 else (0.0 if delta == 0 else None)
    return {
        "smd": smd,
        "variance_ratio": vt / vc if vc > 0 else None,
        "smd_status": "defined" if smd is not None else "unequal constants; zero denominator",
    }


def feature_summary(con, column):
    if column not in FEATURES:
        raise ContractError("Only pre-treatment features may enter distribution/balance analysis")
    q = f'"{column}"'
    probabilities = ",".join(str(p) for p in PERCENTILES)
    row = con.execute(f"""SELECT count(*), min({q}), max({q}), avg({q}),
        stddev_samp({q}), var_samp({q}), skewness({q}),
        quantile_cont({q}, [{probabilities}]),
        count(*) FILTER (WHERE {q}=0), count(*) FILTER (WHERE {q}<0),
        count(*) FILTER (WHERE abs({q}-round({q})) <= 1e-9)
        FROM audit_development""").fetchone()
    n, minimum, maximum, mean, std, variance, skew, quantiles, zeros, negatives, integer_like = row
    quantiles = {
        f"p{round(p * 100):02d}": numeric(v) for p, v in zip(PERCENTILES, quantiles, strict=True)
    }
    iqr = quantiles["p75"] - quantiles["p25"]
    lower, upper = quantiles["p25"] - 1.5 * iqr, quantiles["p75"] + 1.5 * iqr
    cuts = sorted(set(quantiles.values()))
    cdf_sql = ",".join(f"count(*) FILTER (WHERE {q} <= {cut!r})" for cut in cuts)
    arms = con.execute(
        f"""SELECT treatment, count(*), avg({q}), var_samp({q}),
        {cdf_sql}, count(*) FILTER (WHERE {q} < ? OR {q} > ?)
        FROM audit_development GROUP BY treatment ORDER BY treatment""",
        [lower, upper],
    ).fetchall()
    arm_stats = {}
    histograms = {}
    cdfs = {}
    outliers = 0
    for arm in arms:
        t, size, arm_mean, arm_variance, *counts = arm
        cdf_counts = counts[:-1]
        outliers += counts[-1]
        arm_stats[str(t)] = {
            "rows": size,
            "mean": numeric(arm_mean),
            "variance": numeric(arm_variance),
        }
        cdfs[str(t)] = [v / size for v in cdf_counts]
        # Ties collapse cutoffs. Bins are (-inf,c1], (c1,c2], ..., (clast,+inf).
        previous = 0
        histogram = []
        for count in cdf_counts:
            histogram.append(count - previous)
            previous = count
        histogram.append(size - previous)
        histograms[str(t)] = histogram
    if set(arm_stats) != {"0", "1"}:
        raise ContractError("Development audit requires both treatment arms")
    balance = balance_metrics(arm_stats["0"], arm_stats["1"])
    balance["grid_ecdf_gap"] = max(abs(t - c) for t, c in zip(cdfs["1"], cdfs["0"], strict=True))
    distinct, dominant = con.execute(f"""SELECT count(*), max(n) FROM
        (SELECT count(*) n FROM audit_development GROUP BY {q})""").fetchone()
    return {
        "rows": n,
        "min": numeric(minimum),
        "max": numeric(maximum),
        "mean": numeric(mean),
        "stddev": numeric(std),
        "variance": numeric(variance),
        "skewness": numeric(skew),
        "quantiles": quantiles,
        "iqr": iqr,
        "tukey_lower": lower,
        "tukey_upper": upper,
        "tukey_outlier_rows": outliers,
        "distinct_values": distinct,
        "dominant_value_rows": dominant,
        "dominant_value_share": dominant / n,
        "zero_rows": zeros,
        "negative_rows": negatives,
        "integer_like_rows": integer_like,
        "constant": distinct == 1,
        "low_variance_relative": std is not None and std / max(1.0, abs(mean)) <= 1e-8,
        "zero_iqr": iqr == 0,
        "arms": arm_stats,
        "balance": balance,
        "distribution_cutoffs": cuts,
        "histogram_counts_by_treatment": histograms,
    }


def repeated_vectors(con):
    columns = ",".join(f'"{c}"' for c in FEATURES)
    rows = con.execute(f"""WITH sizes AS (
        SELECT count(*) n FROM audit_development GROUP BY {columns})
        SELECT count(*), sum(n), count(*) FILTER (WHERE n>1),
            coalesce(sum(n) FILTER (WHERE n>1),0), sum(n-1), max(n),
            count(*) FILTER (WHERE n=1), count(*) FILTER (WHERE n=2),
            count(*) FILTER (WHERE n BETWEEN 3 AND 5),
            count(*) FILTER (WHERE n BETWEEN 6 AND 10),
            count(*) FILTER (WHERE n BETWEEN 11 AND 100), count(*) FILTER (WHERE n>100)
        FROM sizes""").fetchone()
    names = [
        "distinct_vectors",
        "rows",
        "repeated_vector_groups",
        "rows_in_repeated_vectors",
        "excess_rows_over_distinct_vectors",
        "max_multiplicity",
    ]
    result = dict(zip(names, rows[:6], strict=True))
    result["group_multiplicity_buckets"] = dict(
        zip(["1", "2", "3-5", "6-10", "11-100", ">100"], rows[6:], strict=True)
    )
    return result


def stratum_counts(con, relation="audit_development"):
    # Relation names are internal constants, not user SQL.
    if relation not in {"audit_development", "audit_partition"}:
        raise ContractError("Invalid audit relation")
    counts = {
        (t, v): n
        for t, v, n in con.execute(
            f"SELECT treatment, visit, count(*) FROM {relation} GROUP BY treatment,visit"
        ).fetchall()
    }
    return {f"T{t}_V{v}": counts.get((t, v), 0) for t in (0, 1) for v in (0, 1)}


def development_strata(con, registry):
    output = {"development": stratum_counts(con), "splits": []}
    for entry in registry["development_splits"]:
        part = {"seed": entry["seed"]}
        for role in ("train", "validation"):
            ids = get_member(entry[role], registry["rows"])
            con.register("_audit_partition_ids", pa.table({"row_id": ids}))
            con.execute("""CREATE OR REPLACE TEMP VIEW audit_partition AS
                SELECT d.row_id, d.treatment, d.visit FROM audit_development d
                JOIN _audit_partition_ids m USING(row_id)""")
            part[role] = stratum_counts(con, "audit_partition")
            if sum(part[role].values()) != entry[role]["rows"]:
                raise ContractError("Development split counts do not match frozen membership")
        for key, value in output["development"].items():
            if part["train"][key] + part["validation"][key] != value:
                raise ContractError("Development split strata do not cover development")
        output["splits"].append(part)
    return output


def audit(config, progress=None):
    progress = progress or (lambda _: None)
    before = protected_snapshot(config)
    archive = before[source_path(config).as_posix()]
    if (
        archive["bytes"] != config["data"]["size_bytes"]
        or archive["sha256"] != config["data"]["sha256"]
    ):
        raise ContractError("Raw archive identity changed; refusing development audit")
    registry = json.loads(Path(config["experiment"]["split_registry"]).read_text())
    result = {
        "audit_version": 1,
        "scope": "frozen development records only",
        "source": identity(config),
        "features": {},
        "created_at_utc": now(),
        "registry_sha256": file_sha256(config["experiment"]["split_registry"]),
        "development_membership_sha256": registry["memberships"]["development"]["sha256"],
        "resources": config["resources"],
        "duckdb_version": duckdb.__version__,
        "numpy_version": np.__version__,
        "rows_modified": 0,
        "treatment_effects_or_models_computed": False,
        "holdout_outcome_analysis": False,
    }
    try:
        with connection(config) as con:
            progress("Materializing verified development records only")
            relation = development_relation(con, config)
            relation.create_view("_development_boundary")
            con.execute(
                "CREATE TEMP TABLE audit_development AS SELECT * FROM _development_boundary"
            )
            rows, unique_ids = con.execute(
                "SELECT count(*), count(DISTINCT row_id) FROM audit_development"
            ).fetchone()
            if rows != registry["memberships"]["development"]["rows"] or unique_ids != rows:
                raise ContractError("Development-only row count/identifier uniqueness failed")
            result["development_rows"] = rows
            missingness = {}
            for column in COLUMNS:
                missing, nonfinite = con.execute(f"""SELECT
                    count(*) FILTER (WHERE "{column}" IS NULL),
                    count(*) FILTER (WHERE NOT isfinite("{column}"::DOUBLE))
                    FROM audit_development""").fetchone()
                missingness[column] = {"missing": missing, "nonfinite": nonfinite}
            result["missingness"] = missingness
            if any(v for checks in missingness.values() for v in checks.values()):
                raise ContractError(
                    "Development quality differs from validated finite/nonmissing contract"
                )
            result["arm_rows"] = {
                str(t): n
                for t, n in con.execute(
                    "SELECT treatment,count(*) FROM audit_development GROUP BY treatment"
                ).fetchall()
            }
            for column in FEATURES:
                progress(f"Aggregating {column}")
                result["features"][column] = feature_summary(con, column)
            progress("Counting repeated feature vectors without changing records")
            result["repeated_vectors"] = repeated_vectors(con)
            progress("Counting frozen development split strata")
            result["strata"] = development_strata(con, registry)
    except duckdb.Error as error:
        raise ContractError(
            f"Development audit stopped: {type(error).__name__}; no source was changed"
        ) from None
    after = protected_snapshot(config)
    if before != after:
        raise ContractError("Protected artifacts changed during audit; refusing to publish")
    result["protected_artifacts"] = before
    result["protected_artifacts_unchanged"] = True
    result["status"] = "passed"
    atomic_json(AUDIT_JSON, result)
    write_markdown(result)
    return result


def fmt(value):
    if value is None:
        return "undefined"
    if isinstance(value, int):
        return f"{value:,}"
    return f"{value:.6g}"


def md_table(headers, rows):
    return "\n".join(
        ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
        + [
            "| " + " | ".join(fmt(v) if not isinstance(v, str) else v for v in row) + " |"
            for row in rows
        ]
    )


def write_markdown(report):
    n = report["development_rows"]
    features = report["features"]
    ordered = sorted(features, key=lambda c: abs(features[c]["balance"]["smd"] or 0), reverse=True)
    worst = ordered[0]
    dup = report["repeated_vectors"]
    high_skew = [
        c for c, s in features.items() if s["skewness"] is not None and abs(s["skewness"]) > 1
    ]
    zero_iqr = [c for c, s in features.items() if s["zero_iqr"]]
    low_var = [c for c, s in features.items() if s["low_variance_relative"]]
    max_grid_gap = max(s["balance"]["grid_ecdf_gap"] for s in features.values())
    repeated_share = 100 * dup["rows_in_repeated_vectors"] / n
    excess_share = 100 * dup["excess_rows_over_distinct_vectors"] / n
    grid_feature = max(features, key=lambda c: features[c]["balance"]["grid_ecdf_gap"])
    variance_feature = max(features, key=lambda c: features[c]["balance"]["variance_ratio"] or 0)
    max_smd = abs(features[worst]["balance"]["smd"] or 0)
    nonconstant_zero_iqr = [c for c in zero_iqr if not features[c]["constant"]]
    high_mass = [c for c, summary in features.items() if summary["dominant_value_share"] >= 0.95]
    lines = [
        "# Development data audit — Phase 4",
        "",
        f"Analyzed **{n:,} frozen development records only**. No source records were changed; "
        "no treatment effect, model, uplift estimate, or holdout outcome analysis was computed.",
        "",
        "## Identity and access boundary",
        "",
        f"Source SHA-256: `{report['source']['sha256']}`. Frozen registry SHA-256: "
        f"`{report['registry_sha256']}`. Development membership SHA-256: "
        f"`{report['development_membership_sha256']}`.",
        "",
        "The verified development membership join was materialized before analytical aggregation. "
        "Every audit query uses that development table. Holdout IDs are read only for integrity "
        "and disjointness checks; no holdout label or feature summary is requested. All "
        f"{len(report['protected_artifacts'])} protected source, membership, registry and Phase 3 "
        "provenance files had identical size and SHA-256 before and after the audit.",
        "",
        "## Development sizes and frozen strata",
        "",
        md_table(
            ["Treatment assignment", "Development rows"],
            [
                ["Control (T=0)", report["arm_rows"]["0"]],
                ["Treated (T=1)", report["arm_rows"]["1"]],
            ],
        ),
        "",
        "Counts below describe the predeclared treatment × visit strata. They are not "
        "treatment-effect estimates; no arm visit-rate difference or inference is calculated.",
        "",
    ]
    strata_rows = [["Development", *report["strata"]["development"].values()]]
    for entry in report["strata"]["splits"]:
        for role in ("train", "validation"):
            strata_rows.append([f"{entry['seed']} {role}", *entry[role].values()])
    lines += [
        md_table(["Partition", "T0 V0", "T0 V1", "T1 V0", "T1 V1"], strata_rows),
        "",
        "## Feature summaries and distributions",
        "",
        "All 12 f0–f11 features are anonymized pre-treatment numeric predictors; "
        "no business meanings are assigned. Standard deviation is sample-based. Percentiles "
        "are exact continuous quantiles computed one feature at a time.",
        "",
        md_table(
            ["Feature", "Mean", "SD", "Min", "P01", "P25", "Median", "P75", "P99", "Max"],
            [
                [
                    c,
                    s["mean"],
                    s["stddev"],
                    s["min"],
                    s["quantiles"]["p01"],
                    s["quantiles"]["p25"],
                    s["quantiles"]["p50"],
                    s["quantiles"]["p75"],
                    s["quantiles"]["p99"],
                    s["max"],
                ]
                for c, s in features.items()
            ],
        ),
        "",
        "Additional P05/P10/P90/P95 values and arm-specific histogram counts are in "
        "`reports/data_audit.json`. Bins use unique pooled percentile cutoffs with "
        "right-closed intervals; ties collapse duplicate cutoffs. No rows are sampled.",
        "",
        "## Missingness and numeric patterns",
        "",
        md_table(
            ["Raw field", "Missing", "Nonfinite"],
            [[c, s["missing"], s["nonfinite"]] for c, s in report["missingness"].items()],
        ),
        "",
        md_table(
            [
                "Feature",
                "Distinct",
                "Skewness",
                "Zero %",
                "Negative %",
                "Integer-like %",
                "Dominant value %",
                "Tukey tail %",
                "IQR",
            ],
            [
                [
                    c,
                    s["distinct_values"],
                    s["skewness"],
                    100 * s["zero_rows"] / n,
                    100 * s["negative_rows"] / n,
                    100 * s["integer_like_rows"] / n,
                    100 * s["dominant_value_share"],
                    100 * s["tukey_outlier_rows"] / n,
                    s["iqr"],
                ]
                for c, s in features.items()
            ],
        ),
        "",
        "Skewness is DuckDB's bias-corrected sample Fisher–Pearson coefficient. Integer-like "
        "means absolute distance to the nearest integer ≤1e-9. Dominant value share uses "
        "exact value counts. Tukey tails fall strictly outside [Q1−1.5×IQR, Q3+1.5×IQR]; "
        "these are descriptive flags, not invalid records. Zero IQR, especially with discrete "
        "or concentrated values, can make a large tail fraction unsurprising. Negative values "
        "and repeated numeric levels have no known semantic interpretation.",
        "",
        f"Measured flags: |skewness| > 1: **{', '.join(high_skew) or 'none'}**; "
        f"zero IQR: **{', '.join(zero_iqr) or 'none'}**; relative low variance: "
        f"**{', '.join(low_var) or 'none'}**. Low variance is defined as "
        "SD/max(1,|mean|) ≤1e-8 and is scale-dependent; exact constants are separately recorded. "
        "These flags do not select or remove features.",
        "",
        "## Treatment/control covariate balance",
        "",
        md_table(
            ["Feature", "Control mean", "Treated mean", "SMD", "Variance T/C", "ECDF grid gap"],
            [
                [
                    c,
                    s["arms"]["0"]["mean"],
                    s["arms"]["1"]["mean"],
                    s["balance"]["smd"],
                    s["balance"]["variance_ratio"],
                    s["balance"]["grid_ecdf_gap"],
                ]
                for c, s in features.items()
            ],
        ),
        "",
        "SMD=(mean_T−mean_C)/sqrt((sample variance_T+sample variance_C)/2). "
        "It describes feature imbalance, not an outcome effect. |SMD|≈0.1 is a conventional "
        "screening reference, not a randomization proof or an automatic pass/fail rule. "
        "For equal constants SMD is zero; unequal constants with a zero denominator are "
        "undefined. Variance ratio is undefined when control variance is zero.",
        "",
        "ECDF grid gap is the largest absolute treatment/control cumulative-probability "
        "difference at pooled P01/P05/P10/P25/P50/P75/P90/P95/P99 cutoffs. Counts at these "
        "cutoffs are exact, but the grid maximum is a **lower bound on the full two-sample "
        "KS distance**, not an exact KS statistic or p-value. It checks distribution shape "
        "beyond a mean comparison, while variance ratios check dispersion. With millions "
        "of records, magnitude is more informative here than tiny significance p-values.",
        "",
        f"Largest measured absolute SMD: **{worst}: {fmt(features[worst]['balance']['smd'])}**. "
        f"Largest measured ECDF grid gap: **{fmt(max_grid_gap)}**. "
        "Small marginal gaps would not establish joint balance, known per-experiment "
        "propensities, or advertiser-wide validity.",
        "",
        "## Repeated feature vectors",
        "",
        md_table(
            ["Measure", "Count"],
            [[k.replace("_", " "), v] for k, v in dup.items() if k != "group_multiplicity_buckets"],
        ),
        "",
        md_table(
            ["Vector multiplicity", "Number of distinct vector groups"],
            list(dup["group_multiplicity_buckets"].items()),
        ),
        "",
        f"Rows participating in repeated vectors: **{repeated_share:.6g}%**; "
        f"excess rows over distinct vectors: **{excess_share:.6g}%**. "
        "Grouping uses exact equality of all 12 numeric features, without treatment, outcomes "
        "or exposure. Only aggregate multiplicities are exported. Identical vectors are not "
        "evidence of repeated users: there is no customer key. No observations were "
        "deduplicated. Such vectors may cross row-based development splits; cross-split "
        "vector overlap was not measured, and the frozen splits are not changed.",
        "",
        "## Measured findings and interpretation",
        "",
        f"- All {len(features)} feature summaries cover the full development pool. "
        "There are no missing/nonfinite values in the 16 retained raw fields. "
        "Observed negative values are valid anonymized numbers, "
        "not evidence of impossible records.",
        f"- The largest absolute marginal SMD is {fmt(max_smd)} "
        f"({worst}); the largest measured ECDF grid gap is {fmt(max_grid_gap)} "
        f"({grid_feature}). These describe marginal covariate differences without validating "
        "hidden experimental assignment mechanisms.",
        f"- Dispersion still differs: the largest treated/control variance ratio is "
        f"{fmt(features[variance_feature]['balance']['variance_ratio'])} ({variance_feature}). "
        "A small mean gap should not be read as identical feature distributions.",
        f"- {len(nonconstant_zero_iqr)} nonconstant features have zero IQR. "
        f"Features with at least 95% of observations at one numeric level: "
        f"{', '.join(high_mass) or 'none'}. Dominant mass explains why a percentile summary "
        "or a Tukey flag can be misleading on its own; "
        "inspect the level counts and tails together.",
        f"- {repeated_share:.6g}% of development rows share their full feature vector with "
        "another row. This is a reason to qualify row-independence assumptions, not proof of "
        "duplicated users, and it does not authorize changing the frozen splits.",
        "- All five seeded repetitions have the same stratum sizes because stratification "
        "uses the same parent counts and rounding. Matching stratum counts "
        "do not imply matching memberships; registry hashes establish membership identity.",
        "",
        "## Implications and limitations",
        "",
        "- Preserve all f0–f11 predictors and all observations for the later baseline phase. "
        "Do not invent feature semantics or infer monetary value from feature magnitudes.",
        "- Compare any later scaling, clipping, transformations or feature pruning only inside "
        "the development training/validation protocol. Fit learned preprocessing on training "
        "rows only. This audit fits no transforms and changes no model recipe.",
        "- Skew, concentrated mass, and Tukey tails motivate robust diagnostics and sensitivity "
        "checks; they do not justify deleting anonymous records. Low variance is "
        "scale-dependent and does not by itself establish uselessness.",
        "- Arm sizes differ substantially by design. Later development-only effect and policy "
        "evaluation must quantify uncertainty and watch thin control-event strata. No effect "
        "or uncertainty interval is estimated in Phase 4.",
        "- Exact repeated vectors are preserved; without real entity IDs, row-level splitting "
        "cannot establish entity independence or support customer-level interpretations.",
        "- Privacy subsampling and missing advertiser/experiment IDs limit interpretation. "
        "Marginal covariate balance cannot identify the hidden assignment probabilities. "
        "No temporal generalization, revenue, measured costs, or production impact is inferred.",
        "- The final holdout remains sealed for the single later approved evaluation. "
        "Development diagnostics must not be interpreted as holdout performance.",
        "",
        "## Reproduction and resource limits",
        "",
        "Run `make audit` with the existing verified Phase 3 artifacts. The command refuses "
        "missing/corrupt artifacts and does not reacquire, ingest, split or reconstruct data. "
        "The in-memory DuckDB development table may spill to the ignored cache: one thread, "
        "2 GB query-memory limit and a 6 GB spill ceiling. Exact quantiles and distinct-value "
        "counts are evaluated one feature at a time; no full pandas dataframe is loaded. "
        "Only aggregate JSON and Markdown are published. Raw records, processed data and "
        "membership arrays remain outside Git.",
        "",
    ]
    AUDIT_MD.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", dir=AUDIT_MD.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write("\n".join(lines))
    try:
        temporary.replace(AUDIT_MD)
    finally:
        temporary.unlink(missing_ok=True)
