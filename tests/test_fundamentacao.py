import json

from citizentech_ia.schemas import Occurrence


def test_busca_operacional_devolve_procedimento_em_vez_de_canal_institucional():
    from citizentech_ia.v6.inference import retriever

    chunks = [
        {"chunk_id": "cpfl-reparos:1", "text": "Reparos por equipe técnica; depende do município."},
        {"chunk_id": "operacao:1", "text": "Dados de designação de equipes não são fornecidos nesta POC.",
         "retrieval_terms": "técnico responsável designado equipe despachada ordem serviço empresa executora"},
    ]
    hits = retriever(chunks).search("Qual equipe foi despachada para a ordem de serviço?")
    assert hits[0]["chunk_id"] == "operacao:1"
    assert hits[0]["text"] == chunks[1]["text"]


def test_ajuste_preserva_casos_ids_e_nao_insere_gabarito_na_entrada():
    from citizentech_ia.v3.retrieval import ReviewedRetriever
    from citizentech_ia.v6.inference import SYSTEM, GroundedAnalyzer

    class Counter:
        def count_tokens(self, text):
            return len(text.split())

    occurrence = Occurrence.model_validate({
        "ocorrencia_id": "nao-enviar-rotulo", "simulada": True,
        "pergunta": "Qual custo consta no orçamento?", "relato": "Sem orçamento disponível.",
    })
    analyzer = GroundedAnalyzer(Counter(), ReviewedRetriever([{"chunk_id": "r:1", "text": "Não há orçamento."}]))
    messages, _, _ = analyzer.prepare(occurrence)
    body = json.loads(messages[1]["content"])
    assert messages[0]["content"] == SYSTEM
    assert body["OCORRENCIA"]["pergunta"] == occurrence.pergunta
    assert "ocorrencia_id" not in body["OCORRENCIA"]
    assert "nao-enviar-rotulo" not in str(messages)
    assert set(body) == {"OCORRENCIA", "CONTEXTO"}
