"""Executa um caderno de evidências existentes, sem repetir geração ou treino."""

import json
import os
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "experimentos/v5-1.5b"


def main():
    dest = RUN / "notebooks/06_treinamento_e_avaliacao_1_5b.ipynb"
    if dest.exists():
        raise FileExistsError(dest)
    kernel = RUN / "runs/jupyter/kernels/citizentech-1-5b"
    kernel.mkdir(parents=True, exist_ok=False)
    (kernel / "kernel.json").write_text(json.dumps({
        "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
        "display_name": "CitizenTech1.5B local", "language": "python",
    }))
    os.environ["JUPYTER_PATH"] = str(RUN / "runs/jupyter") + os.pathsep + os.environ.get("JUPYTER_PATH", "")
    nb = nbformat.v4.new_notebook()
    nb.metadata.kernelspec = {
        "name": "citizentech-1-5b", "display_name": "CitizenTech1.5B local", "language": "python",
    }
    md, code = nbformat.v4.new_markdown_cell, nbformat.v4.new_code_cell
    nb.cells = [
        md("# Qwen2.5-1.5B — treinamento e comparação reais\n\n"
           "Este caderno lê evidências já concluídas; não simula respostas nem repete treino. "
           "Dados sintéticos e revisão técnica por IA, sem confirmação humana independente. "
           "As fontes e limitações estão no relatório da versão."),
        code("import json\nfrom pathlib import Path\n"
             "ROOT=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'pyproject.toml').exists())\n"
             "RUN=ROOT/'experimentos/v5-1.5b'\n"
             "def load(path):\n    return json.loads((RUN/path).read_text())\n"
             "from citizentech_ia.datasets import verify_freeze\n"
             "from citizentech_ia.v5.inference import SYSTEM\n"
             "verify_freeze(RUN,system_prompt=SYSTEM)\n"
             "print(json.dumps(load('dados/manifest.json'),ensure_ascii=False,indent=2))"),
        md("## Treinamento e seleção\n\nLoRA FP32 protegido; base FP16 preservada. "
           "Seleção pelos critérios predefinidos da validação64, antes das respostas do teste30. "
           "Validação bruta80 preservada. Pesos finais exatos, sem escolha por melhor loss."),
        code("selection=load('configs/selected.json')\n"
             "print(json.dumps(selection,ensure_ascii=False,indent=2))\n"
             "print(json.dumps(load('docs/smoke-e-estimativa.json'),ensure_ascii=False,indent=2))"),
        md("## Mesmas30 perguntas, três configurações\n\nA:sem contexto. B:RAG simples. C:RAG+LoRA. "
           "B/C recebem as mesmas mensagens e trechos. Status puro e esquema não são acerto semântico."),
        code("for mode in ['final-A','final-B','final-C']:\n"
             "    m=load(f'avaliacao/evidencias/{mode}/metrics.json')\n"
             "    keys=['n','schema_valid_rate','valid_json_and_refs_rate','status_only_match_rate',"
             "'median_seconds','p95_seconds','retrieval_respondible']\n"
             "    print(mode,json.dumps({k:m[k] for k in keys},ensure_ascii=False))"),
        md("## Revisão das respostas\n\nAcerto, alucinação, fundamentação e recusa são julgamentos "
           "técnicos por IA. Incertos ficam no denominador por limites inferior/superior. "
           "Intervalos pareados por família são condicionais aos rótulos e ao conjunto sintético; "
           "não medem erro de anotação nem validade de campo."),
        code("m=load('revisao/test/metrics.json')\n"
             "for mode,s in m['modes'].items():\n"
             "    print(mode,json.dumps({k:s[k] for k in ['n','semantic_correct','integral_accuracy',"
             "'hallucination','refusal_adequate']},ensure_ascii=False))\n"
             "print(json.dumps(m['comparisons'],ensure_ascii=False,indent=2))"),
        md("## Erros e POC\n\nCasos ilustrativos não são um teste independente. HTTP200 valida "
           "transporte e estrutura, não ausência de erro. Não atribuir resultados históricos a este modelo."),
        code("print(json.dumps(load('avaliacao/cinco_erros.json'),ensure_ascii=False,indent=2))\n"
             "print(json.dumps(load('docs/teste-poc-real.json'),ensure_ascii=False,indent=2))"),
        md("## Limites\n\nCorpus com dez procedimentos autorais e duas sínteses institucionais atribuídas. "
           "400/80 herdados da v3; o teste30 foi criado antes destas gerações, mas com autoria/revisão "
           "relacionadas e regras de domínio compartilhadas. Não é conjunto externo independente. "
           "Todos os alvos têm hipóteses causais vazias: a tarefa é triagem, não diagnóstico elétrico. "
           "Teste antigo120 é regressão já observada. Publicação, integração real do grupo, "
           "integrantes/RMs/território, vídeo e revisão humana continuam pendentes. "
           "Consulte o relatório para erros remanescentes e reprodução."),
    ]
    NotebookClient(nb, timeout=120, kernel_name="citizentech-1-5b", resources={
        "metadata": {"path": str(ROOT)},
    }).execute()
    nbformat.write(nb, dest)
    print(dest)


if __name__ == "__main__":
    main()
