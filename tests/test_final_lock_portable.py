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
