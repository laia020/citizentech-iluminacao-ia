import json

import pytest
from fastapi.testclient import TestClient

from citizentech_ia.v5 import service


def forbidden(*args, **kwargs):
    raise AssertionError("Preparação não pode carregar ou executar o modelo.")


def test_sem_adaptador_poc_informa_indisponibilidade_e_nao_usa_modelo_base(tmp_path, monkeypatch):
    monkeypatch.setattr(service, "Generator", forbidden)
    app = service.create_model_app(tmp_path)
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/ready").status_code == 503
        page = client.get("/demo")
        assert page.status_code == 200
        assert "1.5B" in page.text
        response = client.post(
            "/v1/analisar",
            json={
                "ocorrencia_id": "PREPARACAO",
                "pergunta": "Qual análise é possível?",
                "simulada": True,
                "relato": "Luminária pública observada apagada.",
            },
        )
        assert response.status_code == 503
        assert response.json()["codigo"] == "modelo_indisponivel"


def test_adaptador_divergente_e_recusado_antes_de_carregar_pesos(tmp_path, monkeypatch):
    (tmp_path / "configs").mkdir()
    (tmp_path / "adapter").mkdir()
    (tmp_path / "adapter/adapters.safetensors").write_bytes(b"different-weights")
    (tmp_path / "configs/selected.json").write_text(
        json.dumps({"adapter_path": "adapter", "adapter_sha": "not-the-file-sha"})
    )
    (tmp_path / "configs/model.json").write_text(
        json.dumps({"model": "Qwen/Qwen2.5-1.5B-Instruct", "model_path": "absent"})
    )
    monkeypatch.setattr(service, "Generator", forbidden)
    monkeypatch.setattr(service, "verify_freeze", lambda *args, **kwargs: True)
    with pytest.raises(ValueError, match="Adaptador"):
        service.create_model_app(tmp_path)


def test_comando_antigo_nao_inicia_treinamento_historico_sem_opcao_explicita(monkeypatch):
    from citizentech_ia import cli, training

    monkeypatch.setattr(training, "run_training", forbidden)
    monkeypatch.setattr("sys.argv", ["citizentech", "train", "--name", "unexpected", "--lr", "0.0001"])
    with pytest.raises(SystemExit) as result:
        cli.main()
    assert result.value.code == 2
