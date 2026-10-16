"""Streaming continuous moments and paired Gaussian decision uncertainty."""

import numpy as np

from marketing_uplift.data_contract import ContractError
from marketing_uplift.policy_metrics import ranking, reach_bins
from marketing_uplift.robust_metrics import MODELS, gaussian_draws

EVALUATORS = ("ipw", "dr", "s_dr")


def scenario_keys(scenarios):
    return [(method, float(e)) for method in EVALUATORS for e in scenarios]


def basis(t, y, m0, m1, s0, s1):
    return np.column_stack(
        (
            t * y,
            (1 - t) * y,
            m1 - m0,
            t * (y - m1),
            (1 - t) * (y - m0),
            s1 - s0,
            t * (y - s1),
            (1 - t) * (y - s0),
        )
    )


def weights(keys):
    w = np.zeros((len(keys), 8))
    for j, (method, e) in enumerate(keys):
        if not 0 < e < 1:
            raise ContractError("Invalid propensity assumption")
        if method == "ipw":
            w[j, :2] = [1 / e, -1 / (1 - e)]
        elif method in ("dr", "s_dr"):
            offset = 2 if method == "dr" else 5
            w[j, offset : offset + 3] = [1, 1 / e, -1 / (1 - e)]
        else:
            raise ContractError("Unknown evaluator")
    return w


def stream_moments(bins, arrays, keys, batch=65536):
    """Recover all scenario x ranking x six-bin means and covariance of means."""
    n = len(arrays[0])
    if n < 2 or bins.shape != (4, n) or any(len(a) != n for a in arrays):
        raise ContractError("Misaligned decision arrays or insufficient rows")
    code = np.zeros(n, dtype=np.int32)
    for row in bins:
        code = code * 6 + row
    count = np.bincount(code, minlength=1296)
    sums = np.zeros((1296, 8))
    products = np.zeros((1296, 8, 8))
    for start in range(0, n, batch):
        sl = slice(start, start + batch)
        values = basis(*[a[sl] for a in arrays])
        if not np.isfinite(values).all():
            raise ContractError("Nonfinite policy contributions")
        for j in range(8):
            sums[:, j] += np.bincount(code[sl], weights=values[:, j], minlength=1296)
            for k in range(j + 1):
                products[:, j, k] += np.bincount(
                    code[sl], weights=values[:, j] * values[:, k], minlength=1296
                )
                products[:, k, j] = products[:, j, k]
    size = len(keys) * 24
    mean = np.zeros(size)
    centered = np.zeros((size, size))
    seen = 0
    w = weights(keys)
    for cell in np.flatnonzero(count):
        nb = int(count[cell])
        digits = [(cell // 6**k) % 6 for k in (3, 2, 1, 0)]
        active = np.array([s * 24 + m * 6 + digits[m] for s in range(len(keys)) for m in range(4)])
        mapping = np.repeat(w, 4, axis=0)
        cellmean = np.zeros(size)
        cellmean[active] = mapping @ (sums[cell] / nb)
        within = products[cell] - np.outer(sums[cell], sums[cell]) / nb
        centered[np.ix_(active, active)] += mapping @ within @ mapping.T
        delta = cellmean - mean
        centered += np.outer(delta, delta) * seen * nb / (seen + nb)
        mean += delta * nb / (seen + nb)
        seen += nb
    cov = (centered + centered.T) / (2 * n * (n - 1))
    return mean, cov, int((count > 0).sum())


def lower_bands(point, covariance, draws, tolerance):
    se = np.sqrt(np.maximum(np.diag(covariance), 0))
    se[np.diag(covariance) <= tolerance] = 0
    family = np.arange(len(point)) % 6 < 5
    active = family & (se > 0)
    critical = (
        float(np.quantile(np.max(draws[:, active] / se[active], axis=1), 0.95))
        if active.any()
        else 0.0
    )
    return point - critical * se, critical, int(family.sum())


def evaluate(ids, scores, arrays, scenarios, replicates, seed, batch=65536):
    n = len(ids)
    t, y, m0, m1, s0, s1 = arrays
    if not np.isin(t, [0, 1]).all() or not np.isin(y, [0, 1]).all():
        raise ContractError("Invalid assignment/outcome values")
    if any(not np.isfinite(a).all() or np.any((a < 0) | (a > 1)) for a in arrays[2:]):
        raise ContractError("Invalid saved outcome probabilities")
    orders = {m: ranking(scores[m], scores["random"], ids) for m in MODELS}
    bins = np.array([reach_bins(orders[m]) for m in MODELS])
    keys = scenario_keys(scenarios)
    point, cov, cells = stream_moments(bins, arrays, keys, batch)
    draws, numerics = gaussian_draws(cov, replicates, seed)
    lower, critical, family = lower_bands(point, cov, draws, numerics["variance_zero_tolerance"])
    shape = (len(keys), 4, 6)
    support = {}
    for mi, model in enumerate(MODELS):
        support[model] = []
        for k in range(6):
            mask = bins[mi] == k
            support[model].append(
                {
                    "records": int(mask.sum()),
                    "treatment_n": int(t[mask].sum()),
                    "control_n": int((1 - t[mask]).sum()),
                    "treatment_visits": int((t[mask] * y[mask]).sum()),
                    "control_visits": int(((1 - t[mask]) * y[mask]).sum()),
                }
            )
    return {
        "point": point.reshape(shape),
        "lower": lower.reshape(shape),
        "covariance": cov,
        "draws": draws,
        "keys": keys,
        "orders": orders,
        "support": support,
        "rows": n,
        "uncertainty": {
            "replicates": replicates,
            "family_size": family,
            "one_sided_simultaneous_critical": critical,
            "joint_cells": cells,
            **numerics,
        },
    }


def coefficient(evidence, model, k, scenario):
    c = np.zeros(evidence["point"].size)
    if model is not None and k:
        start = scenario * 24 + MODELS.index(model) * 6
        c[start : start + k] = 1
    return c


def summary(evidence, c):
    p = float(c @ evidence["point"].ravel())
    variance = float(c @ evidence["covariance"] @ c)
    tol = evidence["uncertainty"]["variance_zero_tolerance"]
    if variance < -100 * tol:
        raise ContractError("Negative decision comparison variance")
    se = float(np.sqrt(variance)) if variance > tol else 0.0
    shifts = evidence["draws"] @ c if se else np.zeros(len(evidence["draws"]))
    return {
        "estimate": p,
        "per_1000": p * 1000,
        "standard_error": se,
        "pointwise_interval": (p + np.quantile(shifts, [0.025, 0.975])).tolist(),
    }
