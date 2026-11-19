"""Página histórica de RPA: rastreável, acessível sem inferência e presente no pacote."""

import hashlib
import json
import shutil
import subprocess
from html.parser import HTMLParser
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from citizentech_ia.api import create_app
from citizentech_ia.cloud.proxy import create_proxy_app

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/citizentech_ia/v5"
REVISION = "68c69091d9b74afc365573fc3577428f077900de"
EVIDENCE = f"https://github.com/laia020/citizentech-rpa/blob/{REVISION}/docs/evidencias/nuvem-real/"


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.elements = []
        self.text = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))

    def handle_data(self, data):
        self.text.append(data)

    @property
    def links(self):
        return [attrs for tag, attrs in self.elements if tag == "a"]


@pytest.mark.parametrize("ready", [False, True])
def test_pagina_independe_da_prontidao_e_da_fila_da_ia(ready):
    def no_prediction(*args):
        pytest.fail("Consultar evidências não pode executar inferência.")

    app = create_proxy_app(no_prediction, lambda: ready, SOURCE / "demo.html")
    app.state.busy = True
    with TestClient(app) as client:
        result = client.get("/rpa")
        assert result.status_code == 200
        assert result.headers["content-type"].startswith("text/html")
        assert 'lang="pt-BR"' in result.text
        assert "Execução histórica" in result.text
        assert "dados fictícios" in result.text
        assert client.get("/ready").status_code == (200 if ready else 503)
        assert client.get("/demo").status_code == 200
        assert client.get("/", follow_redirects=False).headers["location"] == "/demo"


def test_demo_local_compartilhada_nao_tem_link_para_rota_inexistente():
    app = create_app(None, demo_path=SOURCE / "demo.html")
    app.state.busy = True
    with TestClient(app) as client:
        assert 'href="/rpa"' in client.get("/demo").text
        assert client.get("/rpa").status_code == 200
        assert client.get("/ready").status_code == 503
        paths = client.get("/openapi.json").json()["paths"]
        assert "/v1/analisar" in paths
        assert "/rpa" not in paths


def test_resultados_preservam_contagens_e_identificadores_publicados():
    page = Page((SOURCE / "rpa.html").read_text(encoding="utf-8"))
    metrics = {attrs["data-metrica"]: attrs["data-valor"]
               for _, attrs in page.elements if "data-metrica" in attrs}
    assert metrics == {"entradas": "4", "processados": "2", "duplicados": "1", "pendencias": "1", "falhas": "0"}
    rows = [attrs for tag, attrs in page.elements if tag == "tr" and "data-linha" in attrs]
    assert [(r["data-linha"], r["data-status"]) for r in rows] == [
        ("1", "processado"), ("2", "duplicado"), ("3", "processado"), ("4", "pendente")]
    text = " ".join(page.text)
    assert "333fecbe-114f-4603-824e-43b7fa8dd2d6" in text
    assert "5e25fa23-6c84-423e-87f8-9a1fb4e849d3" in text
    assert "observacao_ausente" in text
    assert "2 chamadas" in text
    assert "18/11/2026" in text
    assert "11:45" in text
    assert "Não consta no resultado exportado" in text


def test_evidencias_fixas_e_navegacao_sem_operacoes_remotas():
    page = Page((SOURCE / "rpa.html").read_text(encoding="utf-8"))
    links = {link.get("href") for link in page.links}
    assert "/demo" in links
    assert "https://github.com/laia020/citizentech-rpa/actions/runs/44327757282" in links
    assert {EVIDENCE + name for name in ["resumo.json", "resultados.json", "auditoria.jsonl"]} <= links
    history = EVIDENCE.replace("nuvem-real/", "real-indisponibilidade/")
    assert {history + name for name in ["resumo.json", "auditoria.jsonl"]} <= links
    assert f"https://github.com/laia020/citizentech-rpa/blob/{REVISION}/output/pdf/relatorio-tecnico-rpa.pdf" in links
    assert not any(tag in {"form", "iframe"} for tag, _ in page.elements)
    scripts = [attrs for tag, attrs in page.elements if tag == "script"]
    assert len(scripts) == 1 and scripts[0].get("id") == "rpa-guide-script"
    assert "src" not in scripts[0]
    ids = [attrs["id"] for _, attrs in page.elements if "id" in attrs]
    assert len(ids) == len(set(ids))
    for _, attrs in page.elements:
        if "aria-labelledby" in attrs:
            assert set(attrs["aria-labelledby"].split()) <= set(ids)
    for link in page.links:
        if link.get("href", "").startswith("#"):
            assert link["href"][1:] in ids
        if link.get("target") == "_blank":
            assert {"noopener", "noreferrer"} <= set(link.get("rel", "").split())
    assert any(tag == "a" and attrs.get("href") == "/rpa" and attrs.get("aria-current") == "page"
               for tag, attrs in page.elements)
    assert any(tag == "a" and attrs.get("href") == "/rpa"
               for tag, attrs in Page((SOURCE / "demo.html").read_text(encoding="utf-8")).elements)


def test_pacote_preserva_pagina_fontes_e_manifesto(tmp_path):
    from scripts.preparar_space import build_bundle

    result = build_bundle(ROOT, tmp_path / "space")
    bundle = Path(result["path"])
    relative = "src/citizentech_ia/v5/rpa.html"
    assert (bundle / relative).read_bytes() == (SOURCE / "rpa.html").read_bytes()
    assert 'href="/rpa"' in (bundle / "cloud-demo.html").read_text(encoding="utf-8")
    assert "situação" in (bundle / "cloud-demo.html").read_text(encoding="utf-8")
    manifest = json.loads((bundle / "bundle-manifest.json").read_text(encoding="utf-8"))
    assert manifest[relative] == hashlib.sha256((bundle / relative).read_bytes()).hexdigest()


def test_apresentacao_identifica_reproducao_e_preserva_alvos_de_navegacao():
    page = Page((SOURCE / "rpa.html").read_text(encoding="utf-8"))
    steps = [attrs for tag, attrs in page.elements if "data-guide-step" in attrs]
    assert len(steps) == 6
    ids = {attrs["id"] for _, attrs in page.elements if "id" in attrs}
    for step in steps:
        assert "hidden" in step
        assert all(selector.strip().removeprefix("#") in ids
                   for selector in step["data-highlight"].split(","))
    assert "Reprodução da execução registrada" in " ".join(page.text)
    assert any(attrs.get("id") == "guide-status" and attrs.get("aria-live") == "polite"
               for _, attrs in page.elements)
    assert any(tag == "noscript" for tag, _ in page.elements)


def test_comportamento_da_apresentacao_em_javascript():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node necessário para verificar o controlador JavaScript, sem dependências de produção.")
    result = subprocess.run([node, "--test", str(ROOT / "tests/rpa_apresentacao.test.cjs")],
                            capture_output=True, text=True, encoding="utf-8", timeout=20)
    assert result.returncode == 0, result.stdout + result.stderr
