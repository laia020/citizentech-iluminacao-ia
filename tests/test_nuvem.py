"""Contratos principais da migração; sem acesso externo ou pesos-base."""

import hashlib
import json
import zipfile

import numpy as np
import pytest
from fastapi.testclient import TestClient
from safetensors.numpy import save

from citizentech_ia.cloud.proxy import create_proxy_app
from citizentech_ia.cloud.weights import load_adapter


def make_bundle(tmp_path):
    artifacts = tmp_path / "artefatos"
    artifacts.mkdir()
    tensors = {
        "model.layers.12.self_attn.q_proj.lora_a": np.ones((4, 2), dtype=np.float32),
        "model.layers.12.self_attn.q_proj.lora_b": np.ones((2, 4), dtype=np.float32),
    }
    weights = save(tensors)
    config = json.dumps({"fine_tune_type": "lora", "num_layers": 1,
                         "lora_parameters": {"rank": 2, "scale": 2, "dropout": .05,
                                             "keys": ["self_attn.q_proj"]}}).encode()
    payload = {"adapters.safetensors": weights, "adapter_config.json": config,
               "BASE-MODEL-LICENSE.txt": b"test fixture"}
    with zipfile.ZipFile(artifacts / "adapter.zip", "w") as archive:
        for name, data in payload.items():
            archive.writestr(name, data)
    manifest = {"model": "Qwen/test", "revision": "fixed", "archive": "adapter.zip",
                "archive_sha": hashlib.sha256((artifacts / "adapter.zip").read_bytes()).hexdigest(),
                "adapter_sha": hashlib.sha256(weights).hexdigest(),
                "files": {name: hashlib.sha256(data).hexdigest() for name, data in payload.items()}}
    (artifacts / "runtime-manifest.json").write_text(json.dumps(manifest))
    selection = tmp_path / "experimentos/v5-1.5b/configs"
    selection.mkdir(parents=True)
    (selection / "selected.json").write_text(json.dumps({"adapter_sha": manifest["adapter_sha"]}))
    (selection / "model.json").write_text(json.dumps({"model": "Qwen/test", "revision": "fixed"}))
    return tmp_path, tensors


def test_cloud_uses_verified_selected_adapter(tmp_path):
    root, expected = make_bundle(tmp_path)
    weights, config, manifest = load_adapter(root)
    assert set(weights) == set(expected)
    assert config["lora_parameters"]["scale"] == 2
    np.testing.assert_array_equal(weights[next(iter(expected))], expected[next(iter(expected))])
    assert manifest["model"] == "Qwen/test"


def test_cloud_rejects_tampered_archive_and_selection(tmp_path):
    root, _ = make_bundle(tmp_path)
    selected = root / "experimentos/v5-1.5b/configs/selected.json"
    selected.write_text(json.dumps({"adapter_sha": "different"}))
    with pytest.raises(ValueError):
        load_adapter(root)
    archive = root / "artefatos/adapter.zip"
    archive.write_bytes(archive.read_bytes() + b"tampered")
    with pytest.raises(ValueError):
        load_adapter(root)


def payload():
    return {"ocorrencia_id": "SIM-001", "pergunta": "O que registrar?",
            "relato": "Luminária apagada à noite.", "simulada": True}


def response():
    return {"status_code": 502, "body": {"request_id": "r1", "codigo": "fonte_incompativel",
                                         "mensagem": "Fonte não sustenta o pedido."}}


def test_proxy_preserves_explicit_upstream_failure(tmp_path):
    page = tmp_path / "demo.html"
    page.write_text("<h1>Akona</h1>")
    seen = []
    app = create_proxy_app(lambda value, headers: (seen.append(value) or response()), lambda: True, page)
    with TestClient(app) as client:
        result = client.post("/v1/analisar", json=payload())
        assert result.status_code == 502
        assert result.json()["codigo"] == "fonte_incompativel"
        assert seen[0]["ocorrencia_id"] == "SIM-001"
        assert client.get("/demo").text == "<h1>Akona</h1>"


def test_proxy_rejects_real_data_and_large_body_without_model(tmp_path):
    seen = []
    app = create_proxy_app(lambda *args: seen.append(args), lambda: True, tmp_path / "unused")
    with TestClient(app) as client:
        assert client.post("/v1/analisar", json={**payload(), "simulada": False}).status_code == 422
        assert client.post("/v1/analisar", content=b"x" * 32769).status_code == 413
        assert client.post("/v1/analisar", json={}).status_code == 422
        assert not seen


def test_proxy_not_ready_and_invalid_remote_output_are_explicit(tmp_path):
    with TestClient(create_proxy_app(lambda *args: {}, lambda: False, tmp_path / "unused")) as client:
        assert client.get("/ready").status_code == 503
        assert client.post("/v1/analisar", json=payload()).status_code == 503
    with TestClient(create_proxy_app(lambda *args: {"status_code": 200, "body": {}},
                                     lambda: True, tmp_path / "unused")) as client:
        assert client.post("/v1/analisar", json=payload()).status_code == 503
