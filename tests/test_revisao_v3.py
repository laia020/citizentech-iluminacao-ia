"""Regressões das causas encontradas na revisão; sem pesos ou GPU."""

import json

from citizentech_ia.schemas import Occurrence


def test_calibracao_v3_mede_relevancia_sem_confundir_com_respondibilidade():
    from citizentech_ia.v3.retrieval import calibrate_relevance

    rows = [
        {"split": "valid", "ranked": [{"chunk_id": "lacuna", "score": 0.4}], "relevant": ["lacuna"]},
        {"split": "valid", "ranked": [{"chunk_id": "ruido", "score": 0.1}], "relevant": []},
    ]
    result = calibrate_relevance(rows)
    assert 0.1 < result["threshold"] <= 0.4
    assert result["recall_at_3"] == 1
    assert result["false_retrieved_chunks"] == 0


def test_busca_v3_considera_pergunta_de_custo_e_sinonimos_de_dano():
    from citizentech_ia.v3.retrieval import ReviewedRetriever, query

    chunks = [
        {
            "chunk_id": "registro:1",
            "text": "Registrar observação.",
            "retrieval_terms": "suporte braço luminária danificado apagada noite",
        },
        {
            "chunk_id": "lacuna:1",
            "text": "Não consta orçamento.",
            "retrieval_terms": "preço custo reparo quanto reais orçamento",
        },
    ]
    r = ReviewedRetriever(chunks)
    o = Occurrence.model_validate(
        {
            "ocorrencia_id": "nao-enviar",
            "simulada": True,
            "pergunta": "Quanto custa o reparo?",
            "relato": "Luminária apagada à noite.",
        }
    )
    assert r.search(query(o))[0]["chunk_id"] == "lacuna:1"
    o = o.model_copy(
        update={"pergunta": "Como registrar a observação?", "relato": "Suporte luminoso danificado."}
    )
    assert r.search(query(o))[0]["chunk_id"] == "registro:1"
    assert r.search(query(o))[0]["text"] == "Registrar observação."


def test_prompt_v3_preserva_pergunta_e_observacoes_sem_ids_ou_rotulos():
    from citizentech_ia.v3.inference import ReviewedAnalyzer
    from citizentech_ia.v3.retrieval import ReviewedRetriever

    class Counter:
        def count_tokens(self, text):
            return len(text.split())

    a = ReviewedAnalyzer(Counter(), ReviewedRetriever([{"chunk_id": "r", "text": "Registrar observação."}]))
    o = Occurrence.model_validate(
        {
            "ocorrencia_id": "test-rotulo",
            "simulada": True,
            "pergunta": "Que pode ser registrado?",
            "relato": "Luz apagada à noite.",
        }
    )
    messages, _, _ = a.prepare(o)
    content = json.loads(messages[1]["content"])
    assert content["OCORRENCIA"]["pergunta"] == o.pergunta
    assert "ocorrencia_id" not in content["OCORRENCIA"]
    assert "test-rotulo" not in str(messages)


def test_revisao_tecnica_nao_se_apresenta_como_revisao_humana():
    from citizentech_ia.v3.review import review_manifest

    m = review_manifest()
    assert m["reviewer_kind"] == "ai_assisted_technical_review"
    assert m["independent_human_review"] is False
