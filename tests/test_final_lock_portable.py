"""Public review identity must not depend on the checkout directory."""

import shutil
from pathlib import Path

from marketing_uplift.final_stage_a import protocol


def test_protocol_identity_survives_checkout_relocation(tmp_path, monkeypatch):
    settings, before, hashes = protocol()
    for filename in hashes:
        source = Path(filename)
        assert not source.is_absolute()
        destination = tmp_path / source
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    monkeypatch.chdir(tmp_path)
    after_settings, after, after_hashes = protocol()
    assert settings == after_settings
    assert hashes == after_hashes and before == after


def test_manifest_cannot_be_substituted_without_changing_approved_lock():
    import copy

    import pytest

    from marketing_uplift.data_contract import ContractError
    from marketing_uplift.final_stage_a import digest, validate_report_binding

    files = {"source.py": "hash"}
    manifest = {"protocol_sha256": "protocol", "models": [{}] * 9}
    protected = {}
    lock = {
        "protocol_sha256": "protocol",
        "model_manifest_sha256": digest(manifest),
        "provenance": {"files": files},
        "protected_snapshot_sha256": digest(protected),
        "stage_b_enabled": False,
        "stage_b_authorized": False,
        "primary": {
            "model": None,
            "ranking": None,
            "reach": 0,
            "advertising_assignments": 0,
            "hypothetical_spending": "0",
            "incremental_gain_relative_to_no_targeting": 0,
            "identity_not_statistical_evidence": True,
            "claim_of_optimality": False,
        },
    }
    report = {
        "protocol_sha256": "protocol",
        "model_manifest": manifest,
        "model_manifest_sha256": digest(manifest),
        "lock": lock,
        "lock_sha256": digest(lock),
        "protected_before": protected,
    }
    validate_report_binding(report, "protocol", files)
    changed = copy.deepcopy(report)
    changed["model_manifest"]["models"][0] = {"different_model": True}
    changed["model_manifest_sha256"] = digest(changed["model_manifest"])
    with pytest.raises(ContractError, match="binding"):
        validate_report_binding(changed, "protocol", files)
    changed = copy.deepcopy(report)
    changed["protected_before"] = {"changed_history": "hash"}
    with pytest.raises(ContractError, match="binding"):
        validate_report_binding(changed, "protocol", files)
