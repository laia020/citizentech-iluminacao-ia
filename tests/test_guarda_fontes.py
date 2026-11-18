from fastapi.testclient import TestClient

from citizentech_ia.api import create_app


def test_pagina_institucional_generica_nao_comprova_designacao_operacional():
    from citizentech_ia.citation_guard import incompatible_citations

    assert incompatible_citations("Qual profissional foi designado?", ["cpfl-reparos:1"]) == ["cpfl-reparos:1"]
    assert incompatible_citations("Qual é o preço exato do reparo?", ["sp-faq:1"]) == ["sp-faq:1"]
    assert incompatible_citations("Qual técnico é responsável?", ["lacuna:1"]) == []
    assert incompatible_citations("Que problemas o serviço de reparos descreve?", ["cpfl-reparos:1"]) == []
    assert incompatible_citations("Qual canal municipal atende?", ["sp-faq:1"]) == []


def test_guarda_rejeita_saida_com_fonte_incompativel_sem_reescrever_resposta():
    from citizentech_ia.citation_guard import attach_guard
    from citizentech_ia.schemas import Analysis

    class Generator:
        ready = True

        def metadata(self):
            return {"modelo": "fake-unitario", "revisao_modelo": "test", "adaptador": "test"}

    class Analyzer:
        generator = Generator()
        mode = "rag_finetuning"
        base_version = "test"
        calls = 0

        def analyze(self, occurrence):
            self.calls += 1
            return {"analysis": Analysis.model_validate({
                "status": "informacao_insuficiente", "resumo": "O documento não identifica o técnico.",
                "hipoteses": [], "informacoes_faltantes": ["Ordem de serviço."],
                "encaminhamento": "Solicitar documento verificável.", "fontes": ["cpfl-reparos:1"],
            }), "chunks": [{"chunk_id": "cpfl-reparos:1", "document_id": "cpfl-reparos", "title": "CPFL", "url": None}]}

    analyzer = Analyzer()
    app = attach_guard(create_app(analyzer))
    with TestClient(app) as client:
        response = client.post("/v1/analisar", json={
            "ocorrencia_id": "TESTE", "pergunta": "Qual técnico foi designado?",
            "relato": "Luz apagada,sem ordem de serviço.", "simulada": True,
        })
    assert response.status_code == 502
    assert response.json()["codigo"] == "fonte_incompativel"
    assert "analise" not in response.json()
    assert analyzer.calls == 1
    assert response.headers["X-Request-ID"] == response.json()["request_id"]


def test_guarda_preserva_resposta_pertinente_e_limites_de_entrada():
    from citizentech_ia.citation_guard import attach_guard
    from citizentech_ia.schemas import Analysis

    class Generator:
        ready = True

        def metadata(self):
            return {"modelo": "fake-unitario", "adaptador": "teste"}

    class Analyzer:
        generator = Generator()
        mode = "rag_finetuning"
        base_version = "teste"

        def analyze(self, occurrence):
            return {"analysis": Analysis.model_validate({
                "status": "informacao_insuficiente", "resumo": "O preço não consta no material.",
                "hipoteses": [], "informacoes_faltantes": ["Orçamento verificável."],
                "encaminhamento": "Solicitar orçamento.", "fontes": ["lacuna:1"],
            }), "chunks": [{"chunk_id": "lacuna:1", "document_id": "lacuna", "title": "Lacuna", "url": None}]}

    with TestClient(attach_guard(create_app(Analyzer()))) as client:
        response = client.post("/v1/analisar", json={
            "ocorrencia_id": "TESTE", "pergunta": "Qual é o preço?", "simulada": True, "relato": "Sem orçamento.",
        })
        assert response.status_code == 200
        assert response.json()["analise"]["fontes"] == ["lacuna:1"]
        assert response.json()["analise"]["resumo"] == "O preço não consta no material."
        assert client.post("/v1/analisar", content=b"x" * 32769).status_code == 413
        assert client.post("/v1/analisar", content=b"not-json").status_code == 422
