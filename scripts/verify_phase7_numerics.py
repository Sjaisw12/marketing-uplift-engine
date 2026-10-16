"""Regenerate small synthetic numerical evidence without any production data."""

from pathlib import Path

import numpy as np

from marketing_uplift.data_contract import atomic_json
from marketing_uplift.robust_metrics import cell_moments, layout, moments


def main():
    rng = np.random.default_rng(8451)
    n = 511
    bins = rng.integers(0, 6, (4, n))
    t, y = rng.integers(0, 2, (2, n))
    m0, m1 = rng.random((2, n))
    keys = layout([0.8, 0.825, 0.85, 0.875, 0.9])
    rows = []
    names = ("random", "response", "s_learner", "t_learner")
    for method, e, name, k in keys:
        pi = (
            np.zeros(n)
            if name == "none"
            else np.ones(n)
            if name == "all"
            else bins[names.index(name)] < k
        )
        if method == "ipw":
            h = pi * t * y / e + (1 - pi) * (1 - t) * y / (1 - e)
        else:
            h = pi * (m1 + t * (y - m1) / e) + (1 - pi) * (m0 + (1 - t) * (y - m0) / (1 - e))
        rows.append(h)
    h = np.array(rows).T
    direct_mean, direct_covariance = h.mean(axis=0), np.cov(h, rowvar=False, ddof=1) / n
    results = []
    for batch in (1, 17, 65536):
        mean, covariance = moments(*cell_moments(bins, t, y, m0, m1, batch), keys)
        mean_error = float(np.max(np.abs(mean - direct_mean)))
        covariance_error = float(np.max(np.abs(covariance - direct_covariance)))
        assert mean_error < 2e-14 and covariance_error < 2e-14
        results.append(
            {
                "batch_rows": batch,
                "maximum_absolute_mean_error": mean_error,
                "maximum_absolute_mean_covariance_error": covariance_error,
            }
        )
    atomic_json(
        Path("reports/phase_7_numerical_reference.json"),
        {
            "fixture": "511 synthetic rows, PCG64 seed8451; independent IPW/DR row formulas",
            "contribution_dimensions": len(keys),
            "covariance_convention": "sample covariance ddof1 / n",
            "interpretation": (
                "Gaussian multiplier covariance equivalence, not exact ordinary row bootstrap"
            ),
            "results": results,
        },
    )


if __name__ == "__main__":
    main()
