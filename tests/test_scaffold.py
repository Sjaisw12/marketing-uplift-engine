"""Fast protocol and command safety checks; these do not validate the dataset."""

import json
import tomllib
from pathlib import Path

import pytest

from marketing_uplift.cli import STAGES, main

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "project.toml"


def test_declared_protocol_keeps_outcomes_out_of_features():
    with CONFIG.open("rb") as stream:
        config = tomllib.load(stream)
    contract = config["contract"]
    assert set(contract["feature_columns"]) == {f"f{i}" for i in range(12)}
    assert not set(contract["feature_columns"]) & set(contract["forbidden_features"])
    assert "exposure" in contract["raw_columns"]
    experiment = config["experiment"]
    assert experiment["outcome"] == "visit"
    assert experiment["holdout_fraction"] == 0.15
    assert experiment["development_validation_fraction"] == 0.20
    assert experiment["stratify_by"] == ["treatment", "visit"]
    assert len(set(experiment["development_seeds"])) == 5


def test_status_is_explicit_about_scaffold_and_does_not_write(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["--config", str(CONFIG), "status"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert "no rows validated or partitions created" in output["implementation"]
    assert output["tracking_uri"] == (tmp_path / "mlruns").as_uri()
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("stage", [stage for stage in STAGES if stage != "acquire"])
def test_unimplemented_stages_fail_without_side_effects(stage, tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as error:
        main([stage])
    assert error.value.code == 2
    assert "not implemented" in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []


def test_missing_configuration_fails_cleanly(tmp_path, capsys):
    with pytest.raises(SystemExit) as error:
        main(["--config", str(tmp_path / "missing.toml"), "status"])
    assert error.value.code == 2
    assert "Configuration or filesystem error" in capsys.readouterr().err
