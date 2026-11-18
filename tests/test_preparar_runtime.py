import hashlib
import json
import zipfile

import pytest

from scripts.preparar_runtime import import_adapter


def fixture(root):
    artifacts = root / "artefatos"
    artifacts.mkdir()
    bundle = artifacts / "adapter.zip"
    payload = {"adapter_config.json": b'{}', "adapters.safetensors": b'test-weights'}
    with zipfile.ZipFile(bundle, "w") as z:
        for name, data in payload.items():
            z.writestr(name, data)
    manifest = {
        "archive": "adapter.zip", "archive_sha": hashlib.sha256(bundle.read_bytes()).hexdigest(),
        "files": {name: hashlib.sha256(data).hexdigest() for name, data in payload.items()},
        "adapter_sha": hashlib.sha256(payload["adapters.safetensors"]).hexdigest(),
    }
    (artifacts / "runtime-manifest.json").write_text(json.dumps(manifest))
    return bundle


def test_importacao_verifica_integridade_e_e_idempotente(tmp_path):
    fixture(tmp_path)
    dest = tmp_path / "adapter"
    import_adapter(tmp_path, dest)
    original = (dest / "adapters.safetensors").read_bytes()
    import_adapter(tmp_path, dest)
    assert (dest / "adapters.safetensors").read_bytes() == original


def test_pacote_alterado_e_recusado_antes_de_gravar(tmp_path):
    bundle = fixture(tmp_path)
    bundle.write_bytes(b"corrupted archive")
    with pytest.raises(ValueError, match="integridade"):
        import_adapter(tmp_path, tmp_path / "adapter")
    assert not (tmp_path / "adapter").exists()


def test_adaptador_existente_diferente_nunca_e_sobrescrito(tmp_path):
    fixture(tmp_path)
    dest = tmp_path / "adapter"
    dest.mkdir()
    (dest / "adapters.safetensors").write_bytes(b"user-existing-weights")
    with pytest.raises(ValueError, match="existente"):
        import_adapter(tmp_path, dest)
    assert (dest / "adapters.safetensors").read_bytes() == b"user-existing-weights"
