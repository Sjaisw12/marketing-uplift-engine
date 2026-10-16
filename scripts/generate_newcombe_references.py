"""Generate offline references using isolated Statsmodels, not project CI code.

Example: .venv/bin/python scripts/generate_newcombe_references.py \
    --reference-path /tmp/phase5-reference-packages
The reference package is deliberately not a project dependency.
"""

import argparse
import hashlib
import inspect
import json
import sys
from decimal import Decimal, localcontext
from pathlib import Path

CASES = [
    ("positive_equal_sizes", 12, 100, 5, 100),
    ("equal_rates", 50, 100, 50, 100),
    ("both_zero_unequal_sizes", 0, 10, 0, 100),
    ("both_all_unequal_sizes", 10, 10, 100, 100),
    ("negative_extreme", 0, 10, 100, 100),
    ("positive_extreme", 10, 10, 0, 100),
    ("small_unequal_sizes", 1, 7, 13, 37),
    ("rare_unequal_sizes", 3, 47, 23, 350),
    ("single_positive", 1, 1, 0, 1),
    ("single_both_all", 1, 1, 1, 1),
    ("single_both_zero", 0, 1, 0, 1),
    ("single_negative", 0, 1, 1, 1),
    ("strong_unequal_sizes", 90, 100, 20, 400),
    ("development_counts", 490301, 10100257, 68089, 1782396),
]
# High-precision normal .975 quantile, independent of binary64 runtime inference.
Z = "1.9599639845400542355245944305205515279555500778695"


def decimal_reference(x1, n1, x0, n0):
    """Solve the Wilson score quadratic at 70-digit precision, then combine limits."""
    with localcontext() as context:
        context.prec = 70
        z2 = Decimal(Z) ** 2

        def roots(events, size):
            x, n = Decimal(events), Decimal(size)
            # (n+z²) theta² - (2x+z²) theta + x²/n = 0.
            a, b, c = n + z2, 2 * x + z2, x * x / n
            discriminant = (b * b - 4 * a * c).sqrt()
            return ((b - discriminant) / (2 * a), (b + discriminant) / (2 * a))

        l1, u1 = roots(x1, n1)
        l0, u0 = roots(x0, n0)
        p1, p0 = Decimal(x1) / Decimal(n1), Decimal(x0) / Decimal(n0)
        difference = p1 - p0
        return [
            str(difference - ((p1 - l1) ** 2 + (u0 - p0) ** 2).sqrt()),
            str(difference + ((u1 - p1) ** 2 + (p0 - l0) ** 2).sqrt()),
        ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-path", type=Path, required=True)
    parser.add_argument(
        "--output", type=Path, default=Path("tests/fixtures/newcombe_wilson_95.json")
    )
    args = parser.parse_args()
    sys.path.insert(0, str(args.reference_path.resolve()))
    import statsmodels
    from statsmodels.stats.proportion import confint_proportions_2indep

    if statsmodels.__version__ != "0.14.5":
        raise RuntimeError("Reference version must be Statsmodels 0.14.5")
    cases = []
    for name, x1, n1, x0, n0 in CASES:
        lower, upper = confint_proportions_2indep(
            x1, n1, x0, n0, method="newcomb", compare="diff", alpha=0.05, correction=False
        )
        decimal = decimal_reference(x1, n1, x0, n0)
        assert max(abs(float(decimal[0]) - lower), abs(float(decimal[1]) - upper)) < 1e-12
        cases.append(
            {
                "name": name,
                "treatment_visits": x1,
                "treatment_n": n1,
                "control_visits": x0,
                "control_n": n0,
                "expected_difference": x1 / n1 - x0 / n0,
                "statsmodels_interval": [float(lower), float(upper)],
                "decimal_interval": decimal,
            }
        )
    reference = {
        "reference_implementation": "statsmodels.stats.proportion.confint_proportions_2indep",
        "version": statsmodels.__version__,
        "source_sha256": hashlib.sha256(
            inspect.getsource(confint_proportions_2indep).encode()
        ).hexdigest(),
        "arguments": {"method": "newcomb", "compare": "diff", "alpha": 0.05, "correction": False},
        "documentation": "https://www.statsmodels.org/v0.14.5/generated/statsmodels.stats.proportion.confint_proportions_2indep.html",
        "independent_check": "70-digit Decimal score roots; no project estimator import",
        "z_975_decimal": Z,
        "absolute_tolerance": 1e-12,
        "cases": cases,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(reference, indent=2) + "\n")
    print(
        f"{len(cases)} Statsmodels cases agree with independent Decimal roots; wrote {args.output}"
    )


if __name__ == "__main__":
    main()
