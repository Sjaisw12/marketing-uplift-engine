"""Frozen, assumption-dependent policy functionals and paired IID uncertainty."""

import math

import numpy as np

from marketing_uplift.data_contract import ContractError

MODELS = ("random", "response", "s_learner")
REACH = np.array([0.1, 0.2, 0.3, 0.4, 0.5])


def weights(t, y, e):
    if not 0 < e < 1:
        raise ContractError("Propensity scenario must be strictly between zero and one")
    return t * y / e - (1 - t) * y / (1 - e)


def ranking(score, priorities, ids):
    if not (len(score) == len(priorities) == len(ids)) or not np.isfinite(score).all():
        raise ContractError("Nonfinite scores or misaligned ranking inputs")
    return np.lexsort((ids, -priorities, -score))


def reach_bins(order):
    n = len(order)
    bins = np.empty(n, dtype=np.uint8)
    ends = [0, *[math.ceil(q * n) for q in REACH], n]
    for k in range(6):
        bins[order[ends[k] : ends[k + 1]]] = k
    return bins


def areas(w, order):
    n = len(w)
    area = float(np.dot(w[order], np.arange(n - 0.5, 0, -1)) / n**2)
    return {"ipw_auuc": area, "ipw_qini_area": area - float(w.mean()) / 2}


def compressed_cells(bins, t, y):
    code = ((bins[0].astype(int) * 6 + bins[1]) * 6 + bins[2]) * 4 + t * 2 + y
    counts = np.bincount(code, minlength=864)
    codes = np.flatnonzero(counts)
    z = codes // 4
    cell_bins = np.array([z // 36, (z // 6) % 6, z % 6])
    return counts[codes], cell_bins, (codes % 4) // 2, codes % 2


def bootstrap_counts(counts, replicates, seed):
    return np.random.default_rng(seed).multinomial(
        int(counts.sum()), counts / counts.sum(), replicates
    )


def intervals(point, replicates):
    return np.quantile(replicates, [0.025, 0.975], axis=0).T.tolist()


def simultaneous(point, replicates):
    sd = replicates.std(axis=0, ddof=1)
    scaled = np.divide(replicates - point, sd, out=np.zeros_like(replicates), where=sd > 1e-15)
    critical = float(np.quantile(np.max(np.abs(scaled), axis=1), 0.95))
    return np.column_stack((point - critical * sd, point + critical * sd)).tolist(), critical


def evaluate(t, y, orders, scenarios, replicates=2000, seed=1):
    """No model fitting or ranking occurs inside bootstrap replicates."""
    bins = np.array([reach_bins(orders[name]) for name in MODELS])
    counts, cb, ct, cy = compressed_cells(bins, t, y)
    draws = bootstrap_counts(counts, replicates, seed)
    policies = np.array([cb[m] < k for m in range(3) for k in range(1, 6)], dtype=float).T
    result = {}
    for e in scenarios:
        w = weights(ct, cy, e)
        base = (1 - ct) * cy / (1 - e)
        contributions = policies * w[:, None] + base[:, None]
        point = counts @ contributions / len(t)
        samples = draws @ contributions / len(t)
        differences = point[10:15] - point[5:10]
        paired = samples[:, 10:15] - samples[:, 5:10]
        bands, critical = simultaneous(differences, paired)
        anchors = np.column_stack((base, ct * cy / e))
        anchor_points = counts @ anchors / len(t)
        anchor_samples = draws @ anchors / len(t)
        policies_out = {}
        for m, name in enumerate(MODELS):
            rows = []
            for k, q in enumerate(REACH):
                selected = bins[m] <= k
                ts, ys = t[selected], y[selected]
                n1, n0 = int(ts.sum()), int((1 - ts).sum())
                x1, x0 = int((ts * ys).sum()), int(((1 - ts) * ys).sum())
                j = m * 5 + k
                rows.append(
                    {
                        "reach": float(q),
                        "selected": int(selected.sum()),
                        "treatment_n": n1,
                        "control_n": n0,
                        "treatment_visits": x1,
                        "control_visits": x0,
                        "selected_arm_rate_difference": x1 / n1 - x0 / n0 if n1 and n0 else None,
                        "low_control_visit_support": x0 < 30,
                        "value": float(point[j]),
                        "value_per_1000": float(point[j] * 1000),
                        "gain_over_none": float(point[j] - anchor_points[0]),
                        "pointwise_value_interval": intervals(point[j], samples[:, j]),
                        "pointwise_gain_interval": intervals(
                            point[j] - anchor_points[0], samples[:, j] - anchor_samples[:, 0]
                        ),
                    }
                )
            policies_out[name] = {"policies": rows, **areas(weights(t, y, e), orders[name])}
        contrasts = {}
        for a, b in ((1, 0), (2, 0), (2, 1)):
            p = point[a * 5 : a * 5 + 5] - point[b * 5 : b * 5 + 5]
            boot = samples[:, a * 5 : a * 5 + 5] - samples[:, b * 5 : b * 5 + 5]
            contrasts[f"{MODELS[a]}_minus_{MODELS[b]}"] = {
                "difference": p.tolist(),
                "pointwise_interval": intervals(p, boot),
            }
        result[str(e)] = {
            "propensity_assumption": e,
            "models": policies_out,
            "anchors": {
                "none": float(anchor_points[0]),
                "all": float(anchor_points[1]),
                "pointwise_intervals": intervals(anchor_points, anchor_samples),
            },
            "paired_contrasts": contrasts,
            "s_minus_response_simultaneous_bands": bands,
            "max_t_critical": critical,
        }
    return {"scenarios": result, "bootstrap_cells": len(counts), "bootstrap_replicates": replicates}
