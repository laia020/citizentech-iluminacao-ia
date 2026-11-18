"""Teste do contrato ASGI com modelo real, sem navegador ou rede externa."""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from citizentech_ia.api import create_app
from citizentech_ia.datasets import verify_freeze
from citizentech_ia.service import local_service

ROOT = Path(__file__).resolve().parents[1]
verify_freeze(ROOT)
analyzer = local_service(ROOT, "adapters/selected/best")
app = create_app(analyzer)
cases = [
    ("registro_minimo", "Luminária apagada durante a noite em via pública."),
    ("observacao", "Luminária observada apagada durante a noite. A causa não foi inspecionada."),
    ("sensor", "LDR sem calibração mede 120 ADC. É possível afirmar o nível em lux e determinar defeito?"),
    ("nao_consta", "Qual é o preço do reparo e o prazo exato de atendimento desta ocorrência?"),
    (
        "conflito",
        "Mesmo instante e ponto: observação visual afirma luz acesa, outro registro comparável afirma apagada.",
    ),
]
report = {
    "transport": "ASGI in-process; sem chamada de navegador/rede",
    "real_model": True,
    "simulated_occurrences": True,
    "group_consumer_integrated": False,
    "semantic_review": "HTTP 200 valida transporte/esquema/referências, não correção semântica; revisão independente pendente.",
    "model": analyzer.generator.metadata(),
    "cases": [],
}
with TestClient(app) as client:
    report["health"] = client.get("/health").status_code
    report["ready"] = client.get("/ready").status_code
    assert report["health"] == report["ready"] == 200
    for case, relato in cases:
        payload = {
            "ocorrencia_id": "DEMO-" + case,
            "pergunta": "Analise as evidências e indique o que falta e o próximo encaminhamento.",
            "simulada": True,
            "relato": relato,
        }
        if case == "sensor":
            payload["sensores"] = [
                {"tipo": "LDR", "valor": 120, "unidade": "ADC", "calibrado": False}
            ]
        elif case == "conflito":
            payload["observacoes_visuais"] = [
                {"descricao": "Luz acesa no mesmo instante e ponto."},
                {"descricao": "Luz apagada no mesmo instante e ponto."},
            ]
        response = client.post(
            "/v1/analisar",
            json=payload,
        )
        row = {"case": case, "input": payload, "http_status": response.status_code, "body": response.json()}
        report["cases"].append(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)
(ROOT / "docs/validacao-api-real.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
if any(r["http_status"] == 503 for r in report["cases"]):
    raise SystemExit("Falha de backend na API real; revisar o relatório.")
print(
    "Contrato com modelo real exercitado. Ver códigos de cada caso; 502 é falha real de geração, não resultado corrigido."
)
