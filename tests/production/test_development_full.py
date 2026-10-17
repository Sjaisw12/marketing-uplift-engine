"""Nine saved models and development probes only; no holdout query/outcomes."""

import json
import tomllib
from pathlib import Path

import numpy as np
import pytest

from marketing_uplift.data_contract import ContractError
from marketing_uplift.splits import get_member
from production_adapter.parquet import ParquetAdapter, ids_sha
from production_adapter.plan import build, verify
from production_adapter.scoring import load_models, read_seal, score_batches

pytestmark = pytest.mark.full_data
ROOT = Path(__file__).resolve().parents[2]


def test_existing_nine_models_on_original_development_probes(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    verify(ROOT)
    plan = build(ROOT)
    registry = json.loads((ROOT / "artifacts/splits.json").read_text())
    development = get_member(registry["memberships"]["development"], registry["rows"])
    model_root = ROOT / plan["model_root"]
    ids = development[np.load(model_root / "probe-positions.npy")]
    config = tomllib.loads((ROOT / "configs/project.toml").read_text())
    adapter = ParquetAdapter(ROOT, plan)
    binding = {"development_verification_only": True, "implementation_sha256": verify(ROOT)}
    m = score_batches(
        adapter.development_features(ids, config),
        ids,
        load_models(ROOT, plan),
        tmp_path / "predictions",
        plan["settings"],
        binding,
        0,
    )
    a = read_seal(tmp_path / "predictions", m, binding, ids_sha(ids))
    response = np.load(model_root / "response-probe-p.npy")
    control = np.load(model_root / "control-probe-p.npy")
    s0 = np.load(model_root / "s_learner-probe-p0.npy")
    s1 = np.load(model_root / "s_learner-probe-p1.npy")
    np.testing.assert_array_equal(
        a["scores"][1:], np.array([response, s1 - s0, response - control])
    )
    for arm in (0, 1):
        expected = np.mean(
            [np.load(model_root / f"nuisance-{k}-{arm}-probe-p.npy") for k in range(3)], axis=0
        )
        np.testing.assert_array_equal(a["nuisance"][arm], expected)
    np.testing.assert_array_equal(a["nuisance"][2:], np.array([s0, s1]))
    # Invalid membership is rejected before opening the Parquet source.
    with pytest.raises(ContractError, match="outside"):
        adapter.development_features(np.array([registry["rows"]], dtype=np.uint64), config)


def test_full_size_invented_checkpoint_export_restore(tmp_path):
    """Local simulation only: validates size handling, not off-workspace transport."""
    from execution_safeguards.checkpoints import snapshot, verify_files
    from execution_safeguards.protocol import digest
    from production_adapter.export import export_chunks, restore_chunks

    source = tmp_path / "invented-source"
    source.mkdir()
    payload_size = 2096939 * 128
    block = b"invented synthetic checkpoint only\n" * 32768
    with (source / "synthetic.bin").open("xb") as out:
        remaining = payload_size
        while remaining:
            piece = block[: min(len(block), remaining)]
            out.write(piece)
            remaining -= len(piece)
    manifest = snapshot(source, ["synthetic.bin"], {"invented_only": True})
    catalog = export_chunks(source, manifest, tmp_path / "parts", reserve_bytes=0)
    assert len(catalog["parts"]) >= 4
    assert max(p["bytes"] for p in catalog["parts"]) <= 67108864
    restored = tmp_path / "restored"
    assert (
        restore_chunks(tmp_path / "parts", restored, digest(catalog), payload_size + 1048576)
        == manifest
    )
    assert verify_files(restored, manifest) == digest(manifest)
