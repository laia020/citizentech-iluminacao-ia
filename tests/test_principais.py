"""Contratos principais escritos antes do código; nenhum teste baixa pesos."""

import json
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from citizentech_ia.api import create_app
from citizentech_ia.datasets import validate_splits
from citizentech_ia.inference import Analyzer, ContextOverflow, InvalidGeneration
from citizentech_ia.retrieval import Retriever, calibrate, retrieval_metrics
from citizentech_ia.schemas import Occurrence


def occurrence(**kwargs):
    return {
        "ocorrencia_id": "SIM-1",
        "pergunta": "Como registrar iluminação apagada?",
        "simulada": True,
        "relato": "Luminária apagada durante a noite.",
        **kwargs,
    }


def answer(**kwargs):
    return {
        "status": "informacao_insuficiente",
        "resumo": "Não é possível determinar a causa.",
        "hipoteses": [],
        "informacoes_faltantes": ["Verificação humana"],
        "encaminhamento": "Solicitar verificação.",
        "fontes": [],
        **kwargs,
    }


CHUNKS = [
    {
        "chunk_id": "geral:1",
        "document_id": "geral",
        "text": "Iluminação apagada à noite: registrar ocorrência para verificação humana.",
        "jurisdiction": None,
        "title": "Triagem",
        "url": None,
    },
    {
        "chunk_id": "sp:1",
        "document_id": "sp",
        "text": "Canal municipal iluminação apagada São Paulo.",
        "jurisdiction": "São Paulo/SP",
        "title": "Municipal",
        "url": "https://example.org",
    },
    {
        "chunk_id": "ldr:1",
        "document_id": "ldr",
        "text": "Sensor LDR bruto ADC sem calibração não mede lux nem comprova defeito.",
        "jurisdiction": None,
        "title": "Sensor",
        "url": None,
    },
]


class Generator:
    ready = True

    def __init__(self, raw=None):
        self.raw = raw or json.dumps(answer())

    def count_tokens(self, text):
        return len(text.split())

    def generate(self, messages, max_tokens):
        return self.raw

    def metadata(self):
        return {"modelo": "fake-unitario", "adaptador": "teste"}


@pytest.mark.parametrize(
    "extra",
    [
        {"observado_em": "2026-11-12T21:00:00"},
        {"extra": 1},
        {"relato": "", "sensores": []},
        {"sensores": [{"tipo": "ldr", "valor": float("nan"), "unidade": "adc", "calibrado": False}]},
        {"sensores": [{"tipo": "ldr", "valor": 10, "unidade": "adc", "calibrado": True}]},
    ],
)
def test_entrada_rejeita_dados_enganosos(extra):
    with pytest.raises(ValidationError):
        Occurrence.model_validate(occurrence(**extra))


def test_recuperacao_preserva_jurisdicao_e_limite():
    r = Retriever(CHUNKS)
    hits = r.search("iluminação apagada noite", threshold=0, k=3)
    assert hits[0]["chunk_id"] == "geral:1"
    assert "sp:1" not in {h["chunk_id"] for h in hits}
    assert len(r.search("sensor LDR calibração ADC", threshold=0.9, k=3)) <= 3
    assert "sp:1" in {
        h["chunk_id"] for h in r.search("São Paulo iluminação", municipality="São Paulo/SP", threshold=0)
    }


def test_recall_nao_e_hit_e_calibracao_so_validacao():
    m = retrieval_metrics(["a", "x", "b"], ["a", "b"])
    assert m["recall@1"] == 0.5 and m["recall@3"] == 1 and m["hit@1"] == 1
    assert retrieval_metrics(["a"], [])["recall@1"] is None
    with pytest.raises(ValueError):
        calibrate([{"split": "test", "score": 1, "answerable": True}])


def test_split_rejeita_familia_repetida():
    rows = [
        {"case_id": "a", "scenario_family": "mesma", "split": "train", "input": occurrence()},
        {
            "case_id": "b",
            "scenario_family": "mesma",
            "split": "test",
            "input": occurrence(relato="Outro texto"),
        },
    ]
    with pytest.raises(ValueError):
        validate_splits(rows)


@pytest.mark.parametrize(
    "raw", ["texto livre", "```json\n{}\n```", json.dumps(answer(fontes=["inexistente"]))]
)
def test_geracao_invalida_nao_e_corrigida_silenciosamente(raw):
    a = Analyzer(Generator(raw), Retriever(CHUNKS), threshold=0)
    with pytest.raises(InvalidGeneration):
        a.analyze(Occurrence.model_validate(occurrence()))


def test_orcamento_nao_trunca_entrada():
    a = Analyzer(Generator(), Retriever(CHUNKS), context_limit=50, max_output=20)
    with pytest.raises(ContextOverflow):
        a.analyze(Occurrence.model_validate(occurrence(relato="dado " * 500)))


def test_api_recusa_valida_e_referencia_fabricada():
    client = TestClient(create_app(Analyzer(Generator(), Retriever(CHUNKS), threshold=0)))
    assert client.get("/health").status_code == 200
    assert client.get("/ready").status_code == 200
    response = client.post("/v1/analisar", json=occurrence())
    assert response.status_code == 200
    assert response.json()["analise"]["status"] == "informacao_insuficiente"
    assert response.json()["execucao"]["modelo"] == "fake-unitario"
    bad = TestClient(
        create_app(
            Analyzer(Generator(json.dumps(answer(fontes=["inventada"]))), Retriever(CHUNKS), threshold=0)
        )
    )
    assert bad.post("/v1/analisar", json=occurrence()).status_code == 502


def test_api_indisponivel_e_corpo_grande():
    c = TestClient(create_app(None))
    assert c.get("/health").status_code == 200
    assert c.get("/ready").status_code == 503
    assert c.post("/v1/analisar", json=occurrence()).status_code == 503
    assert c.post("/v1/analisar", content=b"x" * 33000).status_code == 413


def test_api_ocupada_preserva_health():
    started, release = threading.Event(), threading.Event()

    class Slow(Generator):
        def generate(self, messages, max_tokens):
            started.set()
            assert release.wait(5)
            return self.raw

    c = TestClient(create_app(Analyzer(Slow(), Retriever(CHUNKS), threshold=0)))
    with ThreadPoolExecutor() as executor:
        first = executor.submit(c.post, "/v1/analisar", json=occurrence())
        assert started.wait(3)
        try:
            assert c.get("/health").status_code == 200
            assert c.post("/v1/analisar", json=occurrence()).status_code == 429
        finally:
            release.set()
        assert first.result().status_code == 200


def test_schema_e_referencias_de_hipotese_precisam_corresponder_a_entrada():
    raw = json.dumps(
        answer(
            hipoteses=[
                {
                    "descricao": "Hipótese sem evidência real",
                    "evidencias_observadas": ["sensores.10.valor"],
                    "fontes": ["geral:1"],
                }
            ],
            fontes=["geral:1"],
        )
    )
    a = Analyzer(Generator(raw), Retriever(CHUNKS), threshold=0)
    with pytest.raises(InvalidGeneration):
        a.analyze(Occurrence.model_validate(occurrence()))


def test_demo_disponivel_sem_fingir_modelo_pronto():
    c = TestClient(create_app(None))
    assert "simulados" in c.get("/demo").text
    assert c.get("/ready").status_code == 503
    assert "/v1/analisar" in c.get("/openapi.json").json()["paths"]


def test_revisao_incompleta_nao_vira_metrica_cientifica(tmp_path):
    from citizentech_ia.evaluation import aggregate_review

    d = tmp_path / "runs" / "fake"
    d.mkdir(parents=True)
    (d / "responses.jsonl").write_text('{"case_id":"a"}\n')
    (d / "revisao_humana.csv").write_text(
        "case_id,correto,fundamentado,alucinacao,recusa_adequada,justificativa,revisor\na,,,,,,\n"
    )
    with pytest.raises(ValueError):
        aggregate_review(tmp_path, "fake")


def test_openapi_descreve_resposta_e_erros_para_integracao():
    schema = TestClient(create_app(None)).get("/openapi.json").json()
    response = schema["paths"]["/v1/analisar"]["post"]["responses"]
    assert response["200"]["content"]["application/json"]["schema"]["$ref"].endswith("/AnalysisResponse")
    for status in ["413", "422", "429", "502", "503"]:
        assert response[status]["content"]["application/json"]["schema"]["$ref"].endswith("/ErrorResponse")


def test_metricas_separam_json_classificacao_e_referencia():
    from citizentech_ia.evaluation import grade_structure

    a = Analyzer(Generator(), Retriever(CHUNKS), threshold=0)
    inp = Occurrence.model_validate(occurrence())
    result = grade_structure(a, json.dumps(answer(fontes=["inventada"])), [], inp, "informacao_insuficiente")
    assert result["json_syntax_valid"] and result["schema_valid"] and result["status_match"]
    assert not result["valid_json_and_refs"]


def test_chaves_json_duplicadas_sao_rejeitadas():
    a = Analyzer(
        Generator('{"status":"fora_escopo",' + json.dumps(answer())[1:]), Retriever(CHUNKS), threshold=0
    )
    with pytest.raises(InvalidGeneration):
        a.analyze(Occurrence.model_validate(occurrence()))


def test_identificador_nao_vaza_rotulo_ou_split_para_modelo():
    a = Analyzer(Generator(), Retriever(CHUNKS), threshold=0)
    inp = Occurrence.model_validate(occurrence(ocorrencia_id="test-respondivel-vazamento"))
    messages, _, _ = a.prepare(inp)
    text = json.dumps(messages, ensure_ascii=False)
    assert "test-respondivel-vazamento" not in text
    assert "ocorrencia_id" not in json.loads(messages[1]["content"])["OCORRENCIA"]


def test_congelamento_rejeita_alteracao_do_prompt(tmp_path):
    from citizentech_ia.datasets import verify_freeze

    (tmp_path / "configs").mkdir()
    (tmp_path / "configs/frozen_manifest.json").write_text(
        json.dumps({"artifacts": {}, "system_sha": "prompt-diferente"})
    )
    with pytest.raises(ValueError, match="Prompt"):
        verify_freeze(tmp_path)


def test_congelamento_confere_dados_originais_do_manifesto(tmp_path):
    import hashlib

    from citizentech_ia.datasets import sha, verify_freeze
    from citizentech_ia.inference import SYSTEM

    (tmp_path / "configs").mkdir()
    (tmp_path / "dados").mkdir()
    (tmp_path / "dados/valid.jsonl").write_text("conteudo alterado")
    (tmp_path / "dados/manifest.json").write_text(
        json.dumps({"hashes": {"dados/valid.jsonl": "hash-original"}})
    )
    (tmp_path / "configs/frozen_manifest.json").write_text(
        json.dumps(
            {
                "artifacts": {"dados/manifest.json": sha(tmp_path / "dados/manifest.json")},
                "system_sha": hashlib.sha256(SYSTEM.encode()).hexdigest(),
            }
        )
    )
    with pytest.raises(ValueError, match="dados/valid.jsonl"):
        verify_freeze(tmp_path)


def test_servico_carrega_e_executa_no_mesmo_worker_e_fecha():
    from citizentech_ia.service import ThreadBoundAnalyzer

    owners = []

    class Affine(Analyzer):
        def __init__(self):
            super().__init__(Generator(), Retriever(CHUNKS))
            self.owner = threading.get_ident()

        def analyze(self, occurrence):
            assert threading.get_ident() == self.owner
            owners.append(self.owner)
            return super().analyze(occurrence)

    service = ThreadBoundAnalyzer(Affine)
    with TestClient(create_app(service)) as client:
        for _ in range(2):
            assert client.post("/v1/analisar", json=occurrence()).status_code == 200
    assert len(owners) == 2 and len(set(owners)) == 1
    assert owners[0] != threading.get_ident()
    assert not service.generator.ready
