"""Gera relatório e notebooks exclusivamente a partir de artefatos existentes."""

import json
import os
import sys
from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)


def notebook(filename, title, codes, explanation=""):
    nb = nbf.v4.new_notebook()
    nb.cells = [
        nbf.v4.new_markdown_cell(
            "# "
            + title
            + "\n\nNotebook de análise de artefatos: não inicia downloads ou treinamento. Não substitui revisão humana de fundamentação."
            + "\n\n"
            + explanation
        )
    ]
    nb.cells += [nbf.v4.new_code_cell(code) for code in codes]
    nb.metadata.kernelspec = {
        "display_name": "CitizenTech local",
        "language": "python",
        "name": "citizentech-local",
    }
    NotebookClient(
        nb, timeout=180, kernel_name="citizentech-local", resources={"metadata": {"path": str(ROOT)}}
    ).execute()
    nbf.write(nb, ROOT / "notebooks" / filename)


def build():
    kernel = ROOT / "runs/jupyter/kernels/citizentech-local"
    kernel.mkdir(parents=True, exist_ok=True)
    (kernel / "kernel.json").write_text(
        json.dumps(
            {
                "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
                "display_name": "CitizenTech local",
                "language": "python",
            }
        )
    )
    os.environ["JUPYTER_PATH"] = str(ROOT / "runs/jupyter")
    pre = "import json\nfrom pathlib import Path\n"
    notebook(
        "01_base_e_dados.ipynb",
        "Base e dados",
        [
            pre
            + "manifest=json.loads(Path('dados/manifest.json').read_text()); print(json.dumps(manifest,ensure_ascii=False,indent=2))",
            "from citizentech_ia.datasets import read_jsonl, validate_splits\nrows=[r for p in ['dados/train.jsonl','dados/valid.jsonl','avaliacao/test.jsonl'] for r in read_jsonl(p)]\nprint(validate_splits(rows))\nprint('Documentos:', len(read_jsonl('base/catalogo.jsonl')))\nprint('Trechos:', len(read_jsonl('base/chunks.jsonl')))",
            "from collections import Counter\nfor split in ['train','valid','test']:\n selected=[r for r in rows if r['split']==split]\n print(split, 'categorias:', dict(Counter(r['category'] for r in selected)), 'famílias:', len({r['scenario_family'] for r in selected}))\nprint('Fonte exemplar:', read_jsonl('base/catalogo.jsonl')[0])",
            "p=Path('docs/auditoria-similaridade.json')\nif p.exists():\n audit=json.loads(p.read_text())\n print(audit['method'])\n for pair,summary in audit['comparisons'].items(): print(pair,{k:v for k,v in summary.items() if k!='top_10_pairs'})\n print(audit['limitation'])",
        ],
        "## Método\nOs exemplos são sintéticos e suas famílias estão declaradas. Não representam observações de campo independentes. Código de construção: `src/citizentech_ia/build_data.py`; validação: `citizentech validate-data`. O teste é congelado antes da seleção. A verificação abaixo detecta duplicações exatas e famílias declaradas entre splits, mas não substitui revisão de similaridade semântica.",
    )
    notebook(
        "02_recuperacao.ipynb",
        "Recuperação e limiar",
        [
            pre
            + "r=json.loads(Path('configs/retrieval.json').read_text()); print({k:v for k,v in r.items() if k!='records'})",
            "print('As métricas de recuperação não são acerto da geração. O limiar usa somente validação.')",
            "from citizentech_ia.pipeline import load_retriever\nfrom citizentech_ia.inference import retrieval_query\nfrom citizentech_ia.schemas import Occurrence\nfrom citizentech_ia.datasets import read_jsonl\nfrom citizentech_ia.retrieval import retrieval_metrics\nretriever=load_retriever(Path('.'))\nrecords=[]\nfor row in read_jsonl('dados/valid.jsonl'):\n occurrence=Occurrence.model_validate(row['input'])\n hits=retriever.search(retrieval_query(occurrence),municipality=occurrence.municipio,threshold=r['threshold'])\n records.append({'categoria':row['category'],**retrieval_metrics([h['chunk_id'] for h in hits],row['relevant_chunks'])})\nfor key in ['recall@1','recall@3']:\n values=[x[key] for x in records if x['categoria']=='respondivel' and x[key] is not None]\n print('Validação respondível', key, sum(values)/len(values) if values else None)",
        ],
        "## Método\nTF-IDF combina palavras e caracteres; a busca restringe fontes locais ao município declarado e retorna até três trechos. Limiar escolhido somente na validação. Abaixo, as métricas são recalculadas sem modificar o limiar congelado. Recall de busca e capacidade de responder são medidas diferentes; a calibração de respondibilidade é uma aproximação limitada.",
    )
    notebook(
        "03_fine_tuning.ipynb",
        "Treinamento local e seleção",
        [
            pre
            + "for name in ['smoke-01','lr1e5','lr5e5']:\n p=Path('avaliacao/treinamento')/name/'summary.json'\n if not p.exists(): p=Path('adapters')/name/'summary.json'\n print(name, json.loads(p.read_text()) if p.exists() else 'PENDENTE')",
            "p=Path('configs/selected.json')\nprint(json.dumps(json.loads(p.read_text()),ensure_ascii=False,indent=2) if p.exists() else 'Seleção pendente.')",
            "for name in ['lr1e5','lr5e5']:\n p=Path('avaliacao/treinamento')/name/'provenance.json'\n if not p.exists(): p=Path('adapters')/name/'provenance.json'\n if p.exists():\n  provenance=json.loads(p.read_text())\n  print(name, 'prompt:',provenance.get('prompt_version'), 'versões:',provenance['versions'])\n  print(json.dumps(provenance['settings'],ensure_ascii=False,indent=2))\nprint('Conversas supervisionadas:',json.loads(Path('dados/mlx/manifest.json').read_text()))",
        ],
        "## Execução real e reprodução\nO treinamento foi executado pela CLI local e os registros abaixo são resultados dessa execução, não valores simulados. Implementação: `src/citizentech_ia/training.py`. Para repetir em uma nova rodada, com nome inédito e recursos livres, executar manualmente `citizentech train --name NOVO-NOME --lr 0.00001`. Não reexecutar o orquestrador sobre resultados existentes.\n\nQLoRA sobre base 4 bits, rank 16 nas projeções q/v das últimas 16 camadas. Cada candidato usa 800 microsteps, acumulação 4 e 200 atualizações. A seleção de checkpoint usa validation loss; a seleção entre candidatos usa geração na validação, sem consultar o teste. Contextos supervisionados podem conter fonte de apoio do gabarito, com contagem declarada. Isso não ocorre na avaliação final. Rodadas v1 foram invalidadas por vazamento de identificador; somente v2 participa dos resultados.",
    )
    notebook(
        "04_comparacao.ipynb",
        "Comparação das três configurações",
        [
            pre
            + "p=Path('avaliacao/placar.json')\nresults=json.loads(p.read_text()) if p.exists() else []\nfor m in results:\n print({k:m[k] for k in ['mode','n','json_syntax_valid_rate','schema_valid_rate','valid_json_and_refs_rate','status_match_rate','median_seconds','p95_seconds','semantic_correctness']})\nif not results: print('Experimentos finais pendentes.')",
            "p=Path('avaliacao/cinco_erros.json')\nprint(json.dumps(json.loads(p.read_text()),ensure_ascii=False,indent=2) if p.exists() else 'Erros reais ainda não extraídos.')",
            "for m in results:\n print(m['mode'], 'recuperação respondível:',m.get('retrieval_respondible'))\n print('Por categoria:',json.dumps(m['by_category'],ensure_ascii=False,indent=2))\nprint('Revisão independente: preencher runs/final-*/revisao_humana.csv e então usar citizentech aggregate-review --help. Não preencher resultados sem revisar cada resposta.')",
        ],
        "## Comparação congelada\nA: base sem documentos. B: mesma base com busca. C: mesma base e busca com adaptador selecionado. Todos usam geração gulosa, o mesmo esquema e até 768 tokens. Respostas brutas, prompts e trechos recuperados estão em `avaliacao/respostas/`. Sintaxe, esquema, referências e classificação de status são verificados separadamente. A fundamentação e a alucinação precisam de revisão independente; os valores automáticos não são acurácia semântica.",
    )
    results = (
        json.loads((ROOT / "avaliacao/placar.json").read_text())
        if (ROOT / "avaliacao/placar.json").exists()
        else []
    )
    lines = [
        "# Relatório técnico — Generative AI",
        "",
        "**Integrantes e RMs:** pendentes de fornecimento pelo grupo. **Nome comercial/território:** ainda não definidos.",
        "",
        "## Ficha técnica",
        "",
        "Componente de IA para organizar evidências de iluminação pública e encaminhar ocorrências para revisão humana. Beneficiários: cidadãos afetados por iluminação inadequada; operador direto: equipe de triagem. O produto do grupo integra sensores, visão, dados, automação e interface por contrato. Esta entrega implementa o componente de IA.",
        "",
        "ODS propostos para validação pelo grupo: 11 (espaços urbanos e serviços), 9 (infraestrutura) e 13 (quando houver indicadores reais de redução de desperdício). Nenhum impacto quantitativo foi medido em campo.",
        "",
        "## Arquitetura",
        "",
        "Ocorrência → validação → TF-IDF e seleção por abrangência → até três trechos → Qwen2.5-7B-Instruct quantizado em 4 bits + adaptador → validação JSON/fontes → API/demo. Treinamento e inferência são locais com MLX. Ver SPEC.md e docs/INTEGRACAO.md para o contrato.",
        "",
        "## Fontes e dados",
        "",
        "Tabela completa em docs/FONTES.md e base/fontes.csv. Catálogo: base/catalogo.jsonl; trechos: base/chunks.jsonl. Documentos autorais do protótipo e sínteses atribuídas de SP Regula e CPFL, sem redistribuir páginas integrais. Licenças externas integrais não foram presumidas. Condições de publicação dos materiais autorais devem ser definidas pelo titular.",
        "",
        "Dados: 400 treino, 80 validação, 120 teste; variantes de 72 famílias sintéticas, não medições de campo independentes. O contexto supervisionado do treino pode inserir a fonte-gabarito quando a busca falha; essa informação não é fornecida na avaliação final. Revisão humana independente de gabaritos e fundamentação permanece pendente.",
        "",
        "Auditoria descritiva entre splits em docs/auditoria-similaridade.json: TF-IDF de caracteres sobre relato/pergunta, sem IDs ou gabaritos. Nenhum exemplo atingiu similaridade de cosseno 0,80 com outra divisão. Isso não certifica independência semântica. O relatório não foi usado para modificar dados ou selecionar hiperparâmetros.",
        "",
        "## Resultados automáticos",
        "",
        "| Modo | Casos | JSON e refs válidos | Status válido esperado | Status válido em respondíveis | Mediana (s) | p95 (s) |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for m in results:
        lines.append(
            f"| {m['mode']} | {m['n']} | {m['valid_json_and_refs_rate']:.1%} | {m['status_match_rate']:.1%} | {m['by_category']['respondivel']['status_match_rate']:.1%} | {m['median_seconds']:.2f} | {m['p95_seconds']:.2f} |"
        )
    if not results:
        lines.append("| Experimentos pendentes | — | — | — | — | — | — |")
    lines += [
        "",
        "**As taxas de sintaxe JSON e de esquema aparecem separadamente nos arquivos de métricas e no placar JSON. O status só é comparado após validar o esquema completo; falhas de esquema também reduzem essa taxa. Referências inválidas são pontuadas separadamente. A taxa não é classificação pura nem acerto semântico. Referência existente não prova fundamentação.** Correção, alucinação e adequação da recusa exigem preencher os CSVs de revisão por caso. Nenhuma melhoria científica é declarada com base apenas em loss ou status.",
        "",
        "## Treinamento",
        "",
        "Versão científica v2: identificadores de ocorrência não entram na LLM. Rodadas anteriores com vazamento de categoria foram arquivadas e invalidadas antes do teste final. Ver docs/EVENTOS_EXECUCAO.md.",
        "",
        "Base 4 bits; LoRA rank 16 nas projeções q/v das últimas 16 camadas, com 2,884 milhões de parâmetros treináveis. Pico é memória rastreada pelo MLX, não o consumo completo do macOS.",
        "",
        "| Rodada | Microsteps | Atualizações | Minutos | Pico MLX (GB) | Melhor loss de validação | Passo do melhor checkpoint |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name in ["smoke-01", "lr1e5", "lr5e5"]:
        p = ROOT / "adapters" / name / "summary.json"
        if not p.exists():
            p = ROOT / "avaliacao/treinamento" / name / "summary.json"
        if p.exists():
            m = json.loads(p.read_text())
            lines.append(f"| {name} | {m['microsteps']} | {m['optimizer_updates']} | {m['elapsed_s']/60:.2f} | {m['peak_memory_gb']:.2f} | {m['best_validation_loss']:.5f} | {m['best_iteration']} |")
        else:
            lines.append(f"| {name} | pendente | — | — | — | — | — |")
    selected = ROOT / "configs/selected.json"
    if selected.exists():
        selection = json.loads(selected.read_text())
        lines += ["", f"Adaptador selecionado na validação: **{selection['candidate']}**. Critério: status esperado, esquema/referências e latência. Revisão semântica independente pendente.", ""]
        for name, metric in selection["validation_candidates"].items():
            lines.append(f"- Validação {name}: {metric['status_match_rate']:.2%} de status esperado e {metric['valid_json_and_refs_rate']:.2%} de esquema/referências válidos em {metric['n']} casos.")
        lines += ["", "A prioridade do critério pode escolher um candidato com menos erros de status e mais erros estruturais. Diferenças pequenas em variantes de poucas famílias não demonstram superioridade estatística ou semântica."]
    lines += [
        "",
        "## Cinco erros reais",
        "",
        "Ver avaliacao/cinco_erros.json para saídas brutas e identificadores das execuções. As causas são hipóteses técnicas e as correções propostas precisam de nova validação.",
        "",
        "Interpretação técnica e aceitação local: docs/INTERPRETACAO.md e docs/ACEITACAO.md. Conferência de cobertura, hashes e igualdade de contexto: docs/validacao-entrega.json.",
        "",
        "## Integração e demonstração",
        "",
        "API e cliente de referência pertencem a este componente. Integração com o consumidor real dos colegas, MVP público, vídeo gravado e links de publicação estão pendentes. Teste com cliente de referência não será apresentado como integração final.",
        "",
        "## Reprodutibilidade e limitações",
        "",
        "Ver README.md, uv.lock, configs/frozen_manifest.json e os quatro notebooks com saídas reais. Testes de software não baixam modelos e não simulam evidência de treinamento. Corpus pequeno, exemplos sintéticos e ausência de revisão humana independente limitam inferências sobre generalização. O serviço não comprova causa elétrica nem conformidade normativa e não determina prazo de reparo.",
        "",
        "## Entregas externas pendentes",
        "",
        "Integrantes/RMs, território/nome comercial, integração real do grupo, infra pública, revisão humana dos resultados, vídeo final e autorização para publicação/commits/pushes. Sem essas etapas, não declarar a GS integralmente entregue.",
    ]
    (ROOT / "docs/RELATORIO.md").write_text("\n".join(lines) + "\n")
    print("Relatório e quatro notebooks executados gerados.")


if __name__ == "__main__":
    build()
