"""Frozen Phase 7 continuous policy contributions and Gaussian multiplier inference."""

import numpy as np

from marketing_uplift.data_contract import ContractError
from marketing_uplift.policy_metrics import REACH, areas, ranking, reach_bins, weights

MODELS = ("random", "response", "s_learner", "t_learner")


def basis(t, y, m0, m1):
    return np.column_stack((t * y, (1 - t) * y, m1 - m0, t * (y - m1), (1 - t) * (y - m0), m0))


def layout(scenarios):
    return [
        (method, float(e), name, k)
        for method in ("ipw", "dr")
        for e in scenarios
        for name, k in [("none", 0), ("all", 5), *[(m, k) for m in MODELS for k in range(1, 6)]]
    ]


def coefficients(cell_bins, keys):
    b = np.zeros((len(keys), 6))
    for j, (method, e, name, k) in enumerate(keys):
        selected = name == "all" or (name in MODELS and cell_bins[MODELS.index(name)] < k)
        if method == "ipw":
            b[j, 1] = 1 / (1 - e)
            if selected:
                b[j, 0] = 1 / e
                b[j, 1] = 0
        else:
            b[j, 5] = 1
            b[j, 4] = 1 / (1 - e)
            if selected:
                b[j, 2] = 1
                b[j, 3] = 1 / e
                b[j, 4] = 0
    return b


def cell_moments(bins, t, y, m0, m1, batch=65536):
    code = np.zeros(len(t), dtype=int)
    for row in bins:
        code = code * 6 + row
    counts = np.bincount(code, minlength=1296)
    sums = np.zeros((1296, 6))
    products = np.zeros((1296, 6, 6))
    for start in range(0, len(t), batch):
        sl = slice(start, start + batch)
        v = basis(t[sl], y[sl], m0[sl], m1[sl])
        for j in range(6):
            sums[:, j] += np.bincount(code[sl], weights=v[:, j], minlength=1296)
            for k in range(j + 1):
                products[:, j, k] += np.bincount(
                    code[sl], weights=v[:, j] * v[:, k], minlength=1296
                )
                products[:, k, j] = products[:, j, k]
    return counts, sums, products


def moments(counts, sums, products, keys):
    n = 0
    mean = np.zeros(len(keys))
    m2 = np.zeros((len(keys), len(keys)))
    for code in np.flatnonzero(counts):
        count = int(counts[code])
        z = code
        bins = []
        for _ in range(4):
            bins.append(z % 6)
            z //= 6
        b = coefficients(bins[::-1], keys)
        cellmean = b @ (sums[code] / count)
        within = products[code] - np.outer(sums[code], sums[code]) / count
        delta = cellmean - mean
        m2 += b @ within @ b.T + np.outer(delta, delta) * n * count / (n + count)
        mean += delta * count / (n + count)
        n += count
    if n < 2:
        raise ContractError("Need at least two evaluation rows")
    return mean, (m2 + m2.T) / (2 * n * (n - 1))


def gaussian_draws(covariance, replicates, seed):
    eigen, vectors = np.linalg.eigh(covariance)
    scale = max(float(np.max(np.diag(covariance))), np.finfo(float).tiny)
    if eigen.min() < -1e-10 * scale:
        raise ContractError("Covariance is not positive semidefinite beyond roundoff tolerance")
    factor = vectors * np.sqrt(np.maximum(eigen, 0))
    draws = np.random.default_rng(seed).normal(size=(replicates, len(eigen))) @ factor.T
    return draws, {
        "minimum_eigenvalue": float(eigen.min()),
        "negative_roundoff_eigenvalues": int((eigen < 0).sum()),
        "variance_zero_tolerance": 1e-12 * scale,
    }


def summarize(point, delta, covariance, coefficient, tolerance):
    coefficient = np.asarray(coefficient)
    p = float(coefficient @ point)
    variance = float(coefficient @ covariance @ coefficient)
    if variance < -100 * tolerance:
        raise ContractError("Negative comparison variance")
    se = 0 if variance <= tolerance else np.sqrt(variance)
    shifts = delta @ coefficient if se else np.zeros(len(delta))
    ci = p + np.quantile(shifts, [0.025, 0.975])
    return {"estimate": p, "pointwise_interval": ci.tolist(), "standard_error": float(se)}


def evaluate(t, y, ids, scores, m0, m1, alt0, alt1, scenarios, replicates, seed):
    priorities = scores["random"]
    orders = {name: ranking(scores[name], priorities, ids) for name in MODELS}
    bins = np.array([reach_bins(orders[name]) for name in MODELS])
    keys = layout(scenarios)
    counts, sums, products = cell_moments(bins, t, y, m0, m1)
    point, cov = moments(counts, sums, products, keys)
    draws, numerics = gaussian_draws(cov, replicates, seed)
    tol = numerics["variance_zero_tolerance"]
    index = {key: i for i, key in enumerate(keys)}

    def contrast(*terms):
        c = np.zeros(len(keys))
        for key, value in terms:
            c[index[key]] += value
        return c

    results = {}
    family = []
    for method in ("ipw", "dr"):
        results[method] = {}
        for e in scenarios:
            models = {}
            for name in MODELS:
                rows = []
                for k, q in enumerate(REACH, 1):
                    c = contrast(((method, e, name, k), 1))
                    gain = c - contrast(((method, e, "none", 0), 1))
                    row = {
                        "reach": float(q),
                        "value": summarize(point, draws, cov, c, tol),
                        "gain_over_none": summarize(point, draws, cov, gain, tol),
                        "paired": {},
                    }
                    for other in MODELS:
                        if other == name:
                            continue
                        diff = c - contrast(((method, e, other, k), 1))
                        row["paired"][other] = summarize(point, draws, cov, diff, tol)
                        if e == 0.85 and name == "t_learner" and other == "s_learner":
                            family.append((method, k, diff, row["paired"][other]))
                    rows.append(row)
                models[name] = {"policies": rows}
                if method == "ipw":
                    models[name].update(areas(weights(t, y, e), orders[name]))
            results[method][str(e)] = {
                "models": models,
                "anchors": {
                    name: summarize(point, draws, cov, contrast(((method, e, name, k), 1)), tol)
                    for name, k in [("none", 0), ("all", 5)]
                },
            }
    standardized = []
    for _, _, c, row in family:
        se = row["standard_error"]
        standardized.append(draws @ c / se if se else np.zeros(replicates))
    critical = float(np.quantile(np.max(np.abs(standardized), axis=0), 0.95))
    for _, _, _, row in family:
        p, se = row["estimate"], row["standard_error"]
        row["simultaneous_interval"] = [p - critical * se, p + critical * se]
    sensitivity = {}
    for e in scenarios:
        h0 = alt0 + (1 - t) * (y - alt0) / (1 - e)
        z = alt1 - alt0 + t * (y - alt1) / e - (1 - t) * (y - alt0) / (1 - e)
        sensitivity[str(e)] = {
            "none": float(h0.mean()),
            "all": float((h0 + z).mean()),
            "models": {
                name: [float(h0.mean() + np.sum(z[bins[i] < k]) / len(t)) for k in range(1, 6)]
                for i, name in enumerate(MODELS)
            },
        }
    support = {}
    for i, name in enumerate(MODELS):
        support[name] = {}
        for role in ("cumulative", "band"):
            rows = []
            for k in range(5):
                mask = bins[i] <= k if role == "cumulative" else bins[i] == k
                ts, ys = t[mask], y[mask]
                n1, n0 = int(ts.sum()), int((1 - ts).sum())
                x1, x0 = int((ts * ys).sum()), int(((1 - ts) * ys).sum())
                rows.append(
                    {
                        "reach": float(REACH[k]),
                        "records": int(mask.sum()),
                        "treatment_n": n1,
                        "control_n": n0,
                        "treatment_visits": x1,
                        "control_visits": x0,
                        "low_control_visits": x0 < 30,
                        "selected_arm_rate_difference": x1 / n1 - x0 / n0 if n1 and n0 else None,
                    }
                )
            support[name][role] = rows
    return {
        "estimates": results,
        "s_nuisance_sensitivity": sensitivity,
        "support": support,
        "multiplier_replicates": replicates,
        "joint_cells": int((counts > 0).sum()),
        "simultaneous_family_size": len(family),
        "simultaneous_critical": critical,
        "numerics": numerics,
    }
