"""Array-only final diagnostics; never opens datasets or selects a final policy."""

from itertools import combinations

import numpy as np

from marketing_uplift.data_contract import ContractError
from marketing_uplift.decision_metrics import basis as gain_basis
from marketing_uplift.decision_metrics import scenario_keys, weights
from marketing_uplift.policy_metrics import ranking, reach_bins
from marketing_uplift.robust_metrics import MODELS, gaussian_draws


def cell_statistics(bins, arrays, batch=65536):
    n = len(arrays[0])
    if n < 2 or bins.shape != (4, n) or any(len(a) != n for a in arrays):
        raise ContractError("Invalid final contribution layout")
    code = np.zeros(n, dtype=np.int32)
    for row in bins:
        if np.any(row > 5) or np.any(row < 0):
            raise ContractError("Invalid frozen ranking bins")
        code = code * 6 + row
    counts = np.bincount(code, minlength=1296)
    sums, products = np.zeros((1296, 10)), np.zeros((1296, 10, 10))
    for start in range(0, n, batch):
        sl = slice(start, start + batch)
        a = [v[sl] for v in arrays]
        v = np.column_stack((gain_basis(*a), a[2], a[4]))
        if not np.isfinite(v).all():
            raise ContractError("Nonfinite final contributions")
        for j in range(10):
            sums[:, j] += np.bincount(code[sl], weights=v[:, j], minlength=1296)
            for k in range(j + 1):
                products[:, j, k] += np.bincount(
                    code[sl], weights=v[:, j] * v[:, k], minlength=1296
                )
                products[:, k, j] = products[:, j, k]
    return counts, sums, products


def moments(bins, arrays, keys, batch=65536):
    counts, sums, products = cell_statistics(bins, arrays, batch)
    size, seen = len(keys) * 25, 0
    mean, centered = np.zeros(size), np.zeros((size, size))
    gain_map = np.pad(weights(keys), ((0, 0), (0, 2)))
    baseline_map = np.zeros((len(keys), 10))
    for si, (method, e) in enumerate(keys):
        if method == "ipw":
            baseline_map[si, 1] = 1 / (1 - e)
        else:
            baseline_map[si, 8 if method == "dr" else 9] = 1
            baseline_map[si, 4 if method == "dr" else 7] = 1 / (1 - e)
    for code in np.flatnonzero(counts):
        n = int(counts[code])
        digits = [(code // 6**k) % 6 for k in (3, 2, 1, 0)]
        active, maps = [], []
        for si in range(len(keys)):
            active.extend([si * 25, *[si * 25 + 1 + m * 6 + digits[m] for m in range(4)]])
            maps.extend([baseline_map[si], *[gain_map[si]] * 4])
        active, maps = np.array(active), np.array(maps)
        cellmean = np.zeros(size)
        cellmean[active] = maps @ (sums[code] / n)
        within = products[code] - np.outer(sums[code], sums[code]) / n
        centered[np.ix_(active, active)] += maps @ within @ maps.T
        delta = cellmean - mean
        centered += np.outer(delta, delta) * seen * n / (seen + n)
        mean += delta * n / (seen + n)
        seen += n
    return mean, (centered + centered.T) / (2 * seen * (seen - 1))


def coefficient(si, model=None, reach=0, baseline=False, scenarios=15):
    c = np.zeros(scenarios * 25)
    if baseline:
        c[si * 25] = 1
    if model is not None and reach:
        start = si * 25 + 1 + MODELS.index(model) * 6
        c[start : start + reach] = 1
    return c


def contrast_family(keys):
    labels, rows = [], []
    for si, (method, e) in enumerate(keys):

        def add(name, c):
            labels.append({"evaluator": method, "propensity_assumption": e, "contrast": name})
            rows.append(c)

        for m in MODELS:
            for k in range(1, 6):
                add(f"{m}:{k}_minus_none", coefficient(si, m, k, scenarios=len(keys)))
        for a, b in combinations(MODELS, 2):
            for k in range(1, 6):
                add(
                    f"{a}_minus_{b}:{k}",
                    coefficient(si, a, k, scenarios=len(keys))
                    - coefficient(si, b, k, scenarios=len(keys)),
                )
        add("all_minus_none", coefficient(si, "random", 6, scenarios=len(keys)))
    return labels, np.array(rows)


def uncertainty(point, covariance, matrix, replicates, seed):
    draws, numerics = gaussian_draws(covariance, replicates, seed)
    contrasts = matrix @ point
    variance = np.einsum("ij,ij->i", matrix @ covariance, matrix)
    tolerance = numerics["variance_zero_tolerance"]
    if variance.min() < -100 * tolerance:
        raise ContractError("Negative final contrast variance")
    se = np.where(variance > tolerance, np.sqrt(np.maximum(variance, 0)), 0)
    shifts = draws @ matrix.T
    shifts[:, se == 0] = 0
    critical = (
        float(np.quantile(np.max(np.abs(shifts[:, se > 0] / se[se > 0]), axis=1), 0.95))
        if np.any(se > 0)
        else 0.0
    )
    return {
        "estimate": contrasts,
        "standard_error": se,
        "pointwise_interval": (contrasts + np.quantile(shifts, [0.025, 0.975], axis=0)).T,
        "simultaneous_interval": np.column_stack(
            (contrasts - critical * se, contrasts + critical * se)
        ),
        "critical": critical,
        "numerics": numerics,
        "draws": draws,
    }


def evaluate_arrays(ids, scores, arrays, settings):
    """Pure kernel for synthetic/development tests; not a real holdout interface."""
    n = len(ids)
    if (
        len(np.unique(ids)) != n
        or not np.isin(arrays[0], [0, 1]).all()
        or not np.isin(arrays[1], [0, 1]).all()
    ):
        raise ContractError("Invalid final IDs/labels")
    if any(not np.isfinite(a).all() or np.any((a < 0) | (a > 1)) for a in arrays[2:]):
        raise ContractError("Invalid nuisance probabilities")
    orders = {m: ranking(scores[m], scores["random"], ids) for m in MODELS}
    bins = np.array([reach_bins(orders[m]) for m in MODELS])
    keys = scenario_keys(settings["scenarios"])
    point, cov = moments(bins, arrays, keys, settings["batch_rows"])
    labels, matrix = contrast_family(keys)
    if len(labels) != settings["comparison_family_size"]:
        raise ContractError("Final comparison family mismatch")
    iid = uncertainty(point, cov, matrix, settings["replicates"], settings["multiplier_seed"])
    strat_cov = np.zeros_like(cov)
    strat_point = np.zeros_like(point)
    t, y = arrays[:2]
    support = []
    undefined = False
    for h in range(4):
        mask = 2 * t + y == h
        count = int(mask.sum())
        support.append(count)
        if not count:
            continue
        if count < 2:
            undefined = True
            continue
        p, c = moments(bins[:, mask], [a[mask] for a in arrays], keys, settings["batch_rows"])
        strat_point += count / n * p
        strat_cov += (count / n) ** 2 * c
    stratified = {"status": "undefined_nonempty_stratum_below_two"}
    if not undefined:
        if not np.allclose(strat_point, point, rtol=0, atol=1e-12):
            raise ContractError("Stratified weighted point mismatch")
        stratified = {
            "status": "defined",
            **uncertainty(
                point,
                strat_cov,
                matrix,
                settings["replicates"],
                settings["stratified_multiplier_seed"],
            ),
        }
    return {
        "point": point,
        "covariance": cov,
        "stratified_covariance": strat_cov if not undefined else None,
        "family": labels,
        "iid": iid,
        "stratified": stratified,
        "stratum_counts": support,
        "bins": bins,
        "orders": orders,
        "keys": keys,
    }
