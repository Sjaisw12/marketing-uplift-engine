"""Documentation-only assertions against immutable published aggregate evidence."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_recorded_first_tranche_bindings_cover_all_original_configurations():
    report = json.loads((ROOT / "reports/phase_8_metrics.json").read_text())
    assert len(report["splits"]) == 5
    configurations = candidates = zero = infeasible = 0
    for split in report["splits"]:
        keys = split["scenario_keys"]
        assert len(split["decisions"]) == 8
        for name, decision in split["decisions"].items():
            configurations += 1
            assert decision["model"] is None and decision["reach_index"] == 0
            if name == "zero_value":
                assert decision["reason_codes"] == ["zero_value"]
                zero += 1
            elif name == "below_first_reach":
                assert decision["reason_codes"] == ["no_feasible_positive_reach"]
                infeasible += 1
            else:
                assert len(decision["candidates"]) == 4
                for model, candidate in decision["candidates"].items():
                    candidates += 1
                    assert candidate["accepted_prefix"] == 0
                    assert len(candidate["tranches"]) == 1
                    first = candidate["tranches"][0]
                    assert first["reach_index"] == 1
                    assert keys[first["binding_scenario_index"]] == ["ipw", 0.9]
                    mi = ["random", "response", "s_learner", "t_learner"].index(model)
                    si = first["binding_scenario_index"]
                    assert split["selection"]["marginal_point"][si][mi][0] < 0
                    assert first["worst_lower_net_value"] < 0
                    support = split["selection"]["support"][model][0]
                    assert support["control_n"] and support["treatment_n"]
                    assert support["control_visits"] >= 30
    assert (configurations, zero, infeasible, candidates) == (40, 5, 5, 120)


def test_documented_contrast_table_is_a_rounding_of_saved_values():
    source = ROOT / "reports/portfolio/aggregate_results.json"
    assert hashlib.sha256(source.read_bytes()).hexdigest() == (
        "358c331d72df76d0ca1e4fddd36c7c35be32b1a0b2dd0ae12949c5967ac46169"
    )
    data = json.loads(source.read_text())
    doc = (ROOT / "docs/SCIENTIFIC_RECONCILIATION.md").read_text()
    count = 0
    for row in data["comparisons"]:
        contrast = row["contrast"]
        pairs = {
            "response_minus_s_learner": "Response minus S",
            "response_minus_t_learner": "Response minus T",
            "s_learner_minus_t_learner": "S minus T",
        }
        prefix, _, k = contrast.partition(":")
        if (
            row["evaluator"] == "dr"
            and row["propensity_assumption"] == 0.85
            and row["uncertainty"] == "iid"
            and prefix in pairs
            and k in ("3", "4", "5")
        ):
            lo, hi = row["simultaneous_low_per_1000"], row["simultaneous_high_per_1000"]
            assert lo <= 0 <= hi
            line = (
                f"| {int(k) * 10}% | {pairs[prefix]} | {row['estimate_per_1000']:.6f} | "
                f"[{lo:.6f}, {hi:.6f}] |"
            ).replace("-", "−")
            assert line in doc
            count += 1
    assert count == 9


def test_current_status_and_historical_approval_are_separate():
    doc = " ".join((ROOT / "docs/SCIENTIFIC_RECONCILIATION.md").read_text().split())
    assert "BLOCKED pending owner review" in doc
    assert "Phase 10 PR #15 is merged" in doc
    assert "public website deployment is not claimed" in doc.lower()
    assert "No normalized replacement" in doc
    case = (ROOT / "docs/CASE_STUDY.md").read_text()
    assert "subsequently implemented a local Streamlit dashboard" in case
    assert "**not\nimplemented or claimed**" not in case
