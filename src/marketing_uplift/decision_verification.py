"""Independent read-only Phase 8 evidence gates, plus explicit first-split receipt."""

import json
from pathlib import Path
from urllib.parse import unquote, urlparse

import mlflow
import numpy as np

from marketing_uplift.data_contract import ContractError
from marketing_uplift.decision_engine import apply, choose, counts, feasible, id_hash
from marketing_uplift.decisions import (
    immutable_json,
    inputs,
    protected,
    protocol,
    roles,
    source_outcomes,
)
from marketing_uplift.ingestion import file_sha256
from marketing_uplift.policy_metrics import ranking, reach_bins
from marketing_uplift.robust_metrics import MODELS
from marketing_uplift.splits import get_member, verify_registry


def verify_split(config, report, split):
    settings, digest, _ = protocol()
    if digest != report["protocol_sha256"]:
        raise ContractError("Phase 8 verification protocol mismatch")
    registry = json.loads(Path(config["experiment"]["split_registry"]).read_text())
    spec = next(s for s in registry["development_splits"] if s["seed"] == split["seed"])
    root = Path("artifacts/phase8") / digest
    d = root / str(spec["seed"])
    ids = get_member(spec["validation"], registry["rows"])
    labels = np.load(d / "roles.npy")
    np.testing.assert_array_equal(
        labels, roles(len(ids), spec["seed"] + settings["role_seed_offset"])
    )
    verify_registry(registry)
    for name, sha in split["artifact_hashes"].items():
        if file_sha256(d / name) != sha:
            raise ContractError("Phase 8 verified artifact mismatch")
    if file_sha256(d / "recommendations.json") != split["recommendations_sha256"]:
        raise ContractError("Sealed selection recommendation mismatch")
    # Check logged private copies, not merely run existence.
    mlflow.set_tracking_uri(Path(config["tracking"]["directory"]).resolve().as_uri())
    run = mlflow.get_run(split["mlflow_run_id"])
    assert run.info.status == "FINISHED"
    logged = Path(unquote(urlparse(run.info.artifact_uri).path))
    for name, sha in split["artifact_hashes"].items():
        assert file_sha256(logged / "private_artifacts" / name) == sha
    applications = json.loads((d / "assessment-applications.json").read_text())
    for economic in settings["economics"]:
        decision = split["decisions"][economic["name"]]
        recomputed = choose(
            np.array(split["selection"]["marginal_point"]),
            np.array(split["selection"]["marginal_lower"]),
            split["selection"]["support"],
            economic,
            int((labels == 0).sum()),
            settings["minimum_control_visits"],
        )
        for key in recomputed:
            assert recomputed[key] == decision[key]
        expected = apply(decision, economic, int((labels == 1).sum()))
        for key in expected:
            assert expected[key] == applications[economic["name"]][key]
        assert (
            applications[economic["name"]]["selected_ids_sha256"]
            == split["applications"][economic["name"]]["selected_ids_sha256"]
        )
    max_mean_error, max_variance_error = 0.0, 0.0
    for role, label in (("selection", 0), ("assessment", 1)):
        mask = labels == label
        roleids = ids[mask]
        assert id_hash(roleids) == split["provenance"]["roles"][f"{role}_ids_sha256"]
        scores, (m0, m1, s0, s1) = inputs(spec["seed"], ids, mask)
        t, y = source_outcomes(config, roleids)
        orders = {m: ranking(scores[m], scores["random"], roleids) for m in MODELS}
        bins = {m: reach_bins(order) for m, order in orders.items()}
        with np.load(d / f"{role}-uncertainty.npz") as evidence:
            point, cov, draws, lower = (
                evidence[k] for k in ("point", "covariance", "draws", "lower")
            )
            assert point.shape == (15, 4, 6) and draws.shape == (2000, 360)
            # Direct row-level formulas; no use of production moment/basis functions.
            for si, (method, e) in enumerate(split["scenario_keys"]):
                a, b = (s0, s1) if method == "s_dr" else (m0, m1)
                z = (
                    t * y / e - (1 - t) * y / (1 - e)
                    if method == "ipw"
                    else b - a + t * (y - b) / e - (1 - t) * (y - a) / (1 - e)
                )
                for mi, model in enumerate(MODELS):
                    for k in range(6):
                        values = (bins[model] == k) * z
                        mean, variance = (
                            float(values.mean()),
                            float(values.var(ddof=1) / len(values)),
                        )
                        idx = si * 24 + mi * 6 + k
                        max_mean_error = max(max_mean_error, abs(mean - point[si, mi, k]))
                        max_variance_error = max(max_variance_error, abs(variance - cov[idx, idx]))
                        np.testing.assert_allclose(mean, point[si, mi, k], atol=2e-12, rtol=0)
                        np.testing.assert_allclose(variance, cov[idx, idx], atol=2e-12, rtol=0)
                    # A paired model contrast must agree with direct row variance.
                    paired = ((bins[model] == 0).astype(float) - (bins["s_learner"] == 0)) * z
                    c = np.zeros(360)
                    c[si * 24 + mi * 6] += 1
                    c[si * 24 + 2 * 6] -= 1
                    np.testing.assert_allclose(
                        c @ cov @ c, paired.var(ddof=1) / len(paired), atol=2e-12, rtol=0
                    )
            # Independently reconstruct exact declared300-coordinate max statistic.
            family = np.array([i for i in range(360) if i % 6 < 5])
            tol = split[role]["uncertainty"]["variance_zero_tolerance"]
            variance = np.diag(cov)
            active = family[variance[family] > tol]
            critical = (
                float(
                    np.quantile(np.max(draws[:, active] / np.sqrt(variance[active]), axis=1), 0.95)
                )
                if len(active)
                else 0.0
            )
            se = np.where(variance > tol, np.sqrt(np.maximum(variance, 0)), 0)
            np.testing.assert_allclose(lower.ravel(), point.ravel() - critical * se, atol=1e-13)
            assert critical == split[role]["uncertainty"]["one_sided_simultaneous_critical"]
        n = len(roleids)
        for economic in settings["economics"]:
            application = split["decisions" if label == 0 else "applications"][economic["name"]]
            m, k = application["model"], application["reach_index"]
            count = counts(n)[k]
            assert feasible(economic, n, count)
            selected = np.sort(roleids[orders[m][:count]]) if m else roleids[:0]
            assert id_hash(selected) == application["selected_ids_sha256"]
            assert count == application["ledger"]["selected"]
    return {
        "maximum_direct_mean_error": max_mean_error,
        "maximum_direct_variance_error": max_variance_error,
        "verified_coordinates_per_role": 360,
    }


def verify_first(config):
    report = json.loads(Path("reports/phase_8_first_split.json").read_text())
    if protected(config) != report["protected_before"]:
        raise ContractError("Protected artifacts changed before first-split gate")
    checked = verify_split(config, report, report["splits"][0])
    root = Path("artifacts/phase8") / report["protocol_sha256"]
    resultpath = root / str(report["splits"][0]["seed"]) / "result.json"
    receipt = {
        "result_sha256": file_sha256(resultpath),
        "protocol_sha256": report["protocol_sha256"],
        **checked,
    }
    immutable_json(root / "first-split-gate.json", receipt)
    return receipt
