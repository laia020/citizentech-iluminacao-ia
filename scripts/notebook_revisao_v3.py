"""Caderno executado a partir de evidências existentes; não repete treino/inferência."""

import json
import os
import sys
from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
V3 = ROOT / "experimentos/v3"


def main():
    destination = V3 / "notebooks/05_revisao_dados_respostas.ipynb"
    destination.parent.mkdir(exist_ok=True)
    if destination.exists():
        raise FileExistsError(destination)
    kernel = V3 / "runs/jupyter/kernels/citizentech-v3"
    kernel.mkdir(parents=True, exist_ok=False)
    (kernel / "kernel.json").write_text(
        json.dumps(
            {
                "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
                "display_name": "CitizenTech v3 local",
                "language": "python",
            }
        )
    )
    os.environ["JUPYTER_PATH"] = str(V3 / "runs/jupyter") + os.pathsep + os.environ.get("JUPYTER_PATH", "")
    nb = nbf.v4.new_notebook()
    nb.metadata.kernelspec = {
        "name": "citizentech-v3",
        "display_name": "CitizenTech v3 local",
        "language": "python",
    }
    nb.cells = [
        nbf.v4.new_markdown_cell(
            "# Revisão dos dados e respostas — v3\n\n"
            "Este caderno lê execuções locais reais já concluídas. Não simula respostas nem repete o treinamento. "
            "A revisão semântica é técnica por IA, com confirmação humana independente pendente. "
            "Veja o protocolo e o adendo fixados antes da geração. Os casos são sintéticos."
        ),
        nbf.v4.new_code_cell(
            "import json\nfrom pathlib import Path\n"
            "ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p/'pyproject.toml').exists())\n"
            "V3 = ROOT/'experimentos/v3'\n"
            "def load(path):\n    return json.loads((V3/path).read_text())\n"
            "from citizentech_ia.datasets import verify_freeze\n"
            "from citizentech_ia.v3.inference import SYSTEM\n"
            "from citizentech_ia.v3.analysis_sets import plan\n"
            "verify_freeze(V3, system_prompt=SYSTEM)\n"
            "p, digest = plan(V3)\n"
            "print(json.dumps({'dados': load('dados/manifest.json')['counts'], "
            "'familias_declaradas': load('dados/manifest.json')['families_per_split'], "
            "'conjuntos_sem_sobreposicao_identificada': p['confirmatory_counts'], "
            "'plano_sha': digest, 'revisao_humana_independente': False}, ensure_ascii=False, indent=2))"
        ),
        nbf.v4.new_markdown_cell(
            "## Treinamento e seleção\n\nPesos finais de 800 microsteps; validação sem gradiente. "
            "O adendo substitui a escolha pelo melhor checkpoint de loss. O teste não escolhe o modelo."
            " A tentativa r2 interrompida por NaN é inelegível; a repetição r2s usa FP32, proteção de gradientes "
            "e sementes NumPy/MLX explícitas. Não comparar candidatos como efeito isolado da taxa de aprendizado."
        ),
        nbf.v4.new_code_cell(
            "selection = load('configs/selected.json')\n"
            "print(json.dumps(selection, ensure_ascii=False, indent=2))\n"
            "for path in sorted((V3/'adapters').glob('r*/summary.json')):\n"
            "    print(path.parent.name, json.dumps(json.loads(path.read_text()), ensure_ascii=False))\n"
            "print('Tentativa r2 incompleta:', json.dumps(load('adapters/r2/failure-review.json'), ensure_ascii=False))"
        ),
        nbf.v4.new_markdown_cell(
            "## Três configurações nas mesmas perguntas\n\nA: sem contexto. B: busca e modelo-base. "
            "C: mesma busca e base, com LoRA. Status correto é uma métrica de classificação, não acerto semântico. "
            "Os placares bruto (120) e confirmatório (112) são preservados."
        ),
        nbf.v4.new_code_cell(
            "for mode in ['final-A', 'final-B', 'final-C']:\n"
            "    for filename in ['metrics.json', 'clean_metrics.json']:\n"
            "        m = load(f'runs/{mode}/{filename}')\n"
            "        fields = ['n', 'schema_valid_rate', 'valid_json_and_refs_rate', "
            "'status_only_match_rate', 'median_seconds', 'p95_seconds', 'retrieval_respondible']\n"
            "        print(mode, filename, json.dumps({k: m[k] for k in fields}, ensure_ascii=False))"
        ),
        nbf.v4.new_markdown_cell(
            "## Revisão das respostas brutas\n\nAcerto semântico e alucinação foram anotados separadamente do formato. "
            "Incerto permanece no denominador e produz limites inferior/superior. "
            "Intervalos por família são condicionais a rótulos técnicos por IA e ao conjunto sintético; "
            "não medem erro do revisor ou generalização para campo."
        ),
        nbf.v4.new_code_cell(
            "for filename in ['metrics.json', 'clean_metrics.json']:\n"
            "    m = load(f'revisao/v3/{filename}')\n"
            "    print(filename)\n"
            "    for mode, scores in m['modes'].items():\n"
            "        print(mode, json.dumps({k: scores[k] for k in ['n', 'semantic_correct', "
            "'integral_accuracy', 'hallucination', 'refusal_adequate']}, ensure_ascii=False))\n"
            "    print(json.dumps(m['comparisons'], ensure_ascii=False, indent=2))"
        ),
        nbf.v4.new_markdown_cell(
            "## API e regressões conhecidas\n\nHTTP 200 comprova transporte e validação estrutural; "
            "a análise de conteúdo é separada. Estes casos já eram conhecidos pelo desenvolvimento. "
            "Não substituem teste não visto ou integração com o produto dos colegas."
        ),
        nbf.v4.new_code_cell(
            "report = load('docs/regressao-api-real.json')\n"
            "print(json.dumps({'health': report['health'], 'ready': report['ready'], "
            "'model': report['model'], 'group_consumer_integrated': report['group_consumer_integrated']}, "
            "ensure_ascii=False, indent=2))\n"
            "for case in report['cases']:\n"
            "    print(case['case'], case['http_status'], json.dumps(case['body'], ensure_ascii=False))"
        ),
        nbf.v4.new_markdown_cell(
            "## Limites e reprodução\n\nOs registros de entrada, contexto e saída bruta ficam em runs/final-*/responses.jsonl. "
            "Os julgamentos e justificativas ficam em revisao/v3. O corpus contém procedimentos autorais "
            "identificados e duas sínteses institucionais atribuídas. Não é um laudo elétrico. "
            "A v2 permanece como histórico; comparar v2 e v3 em testes diferentes não isola ganho causal. "
            "A auditoria de cobertura inspecionou recuperação do teste antes da seleção, sem gerar respostas "
            "ou ajustar candidatos; isso impede apresentar dados/recuperação como inteiramente sem inspeção. "
            "A autoria e revisão comuns também impedem classificá-lo como validação cega independente. "
            "Integração real, revisão humana, publicação e vídeo continuam sujeitos às pendências do grupo. "
            "Consulte README.md desta revisão para comandos de reprodução sem sobrescrever resultados."
        ),
    ]
    NotebookClient(
        nb, timeout=120, kernel_name="citizentech-v3", resources={"metadata": {"path": str(ROOT)}}
    ).execute()
    nbf.write(nb, destination)
    print(destination)


if __name__ == "__main__":
    main()
