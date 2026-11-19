# Relatório técnico — Generative AI

**Integrantes e RMs:** pendentes de fornecimento pelo grupo. **Nome comercial/território:** ainda não definidos.

## Ficha técnica

Componente de IA para organizar evidências de iluminação pública e encaminhar ocorrências para revisão humana. Beneficiários: cidadãos afetados por iluminação inadequada; operador direto: equipe de triagem. O produto do grupo integra sensores, visão, dados, automação e interface por contrato. Esta entrega implementa o componente de IA.

ODS propostos para validação pelo grupo: 11 (espaços urbanos e serviços), 9 (infraestrutura) e 13 (quando houver indicadores reais de redução de desperdício). Nenhum impacto quantitativo foi medido em campo.

## Arquitetura

Ocorrência → validação → TF-IDF e seleção por abrangência → até três trechos → Qwen2.5-7B-Instruct quantizado em 4 bits + adaptador → validação JSON/fontes → API/demo. Treinamento e inferência são locais com MLX. Ver SPEC.md e docs/INTEGRACAO.md para o contrato.

## Fontes e dados

Tabela completa em docs/FONTES.md e base/fontes.csv. Catálogo: base/catalogo.jsonl; trechos: base/chunks.jsonl. Documentos autorais do protótipo e sínteses atribuídas de SP Regula e CPFL, sem redistribuir páginas integrais. Licenças externas integrais não foram presumidas. Condições de publicação dos materiais autorais devem ser definidas pelo titular.

Dados: 400 treino, 80 validação, 120 teste; variantes de 72 famílias sintéticas, não medições de campo independentes. O contexto supervisionado do treino pode inserir a fonte-gabarito quando a busca falha; essa informação não é fornecida na avaliação final. Revisão humana independente de gabaritos e fundamentação permanece pendente.

Auditoria descritiva entre splits em docs/auditoria-similaridade.json: TF-IDF de caracteres sobre relato/pergunta, sem IDs ou gabaritos. Nenhum exemplo atingiu similaridade de cosseno 0,80 com outra divisão. Isso não certifica independência semântica. O relatório não foi usado para modificar dados ou selecionar hiperparâmetros.

## Resultados automáticos

| Modo | Casos | JSON e refs válidos | Status válido esperado | Status válido em respondíveis | Mediana (s) | p95 (s) |
|---|---:|---:|---:|---:|---:|---:|
| base_sem_contexto | 120 | 45.8% | 23.3% | 20.0% | 2.54 | 3.59 |
| rag_simples | 120 | 74.2% | 49.2% | 50.0% | 3.01 | 4.10 |
| rag_finetuning | 120 | 93.3% | 65.0% | 75.0% | 2.47 | 2.79 |

**As taxas de sintaxe JSON e de esquema aparecem separadamente nos arquivos de métricas e no placar JSON. O status só é comparado após validar o esquema completo; falhas de esquema também reduzem essa taxa. Referências inválidas são pontuadas separadamente. A taxa não é classificação pura nem acerto semântico. Referência existente não prova fundamentação.** Correção, alucinação e adequação da recusa exigem preencher os CSVs de revisão por caso. Nenhuma melhoria científica é declarada com base apenas em loss ou status.

## Treinamento

Versão científica v2: identificadores de ocorrência não entram na LLM. Rodadas anteriores com vazamento de categoria foram arquivadas e invalidadas antes do teste final. Ver docs/EVENTOS_EXECUCAO.md.

Base 4 bits; LoRA rank 16 nas projeções q/v das últimas 16 camadas, com 2,884 milhões de parâmetros treináveis. Pico é memória rastreada pelo MLX, não o consumo completo do macOS.

| Rodada | Microsteps | Atualizações | Minutos | Pico MLX (GB) | Melhor loss de validação | Passo do melhor checkpoint |
|---|---:|---:|---:|---:|---:|---:|
| smoke-01 | 40 | 10 | 2.09 | 8.38 | 1.38284 | 40 |
| lr1e5 | 800 | 200 | 52.49 | 8.57 | 0.07315 | 800 |
| lr5e5 | 800 | 200 | 54.50 | 8.57 | 0.01823 | 800 |

Adaptador selecionado na validação: **lr1e5**. Critério: status esperado, esquema/referências e latência. Revisão semântica independente pendente.

- Validação lr1e5: 71.25% de status esperado e 93.75% de esquema/referências válidos em 80 casos.
- Validação lr5e5: 70.00% de status esperado e 98.75% de esquema/referências válidos em 80 casos.

A prioridade do critério pode escolher um candidato com menos erros de status e mais erros estruturais. Diferenças pequenas em variantes de poucas famílias não demonstram superioridade estatística ou semântica.

## Cinco erros reais

Ver avaliacao/cinco_erros.json para saídas brutas e identificadores das execuções. As causas são hipóteses técnicas e as correções propostas precisam de nova validação.

Interpretação técnica e aceitação local: docs/INTERPRETACAO.md e docs/ACEITACAO.md. Conferência de cobertura, hashes e igualdade de contexto: docs/validacao-entrega.json.

## Integração e demonstração

API, cliente de referência, demonstração pública e links de publicação pertencem a este componente. O cliente de referência demonstra o contrato HTTP e o tratamento de respostas.

### Vídeos da apresentação

- Vídeo focado em IA: [assistir à demonstração no Google Drive](https://drive.google.com/file/d/1aRLiZTX9kAE6g9fWVuiMmpKt-vXvg-n2/view?usp=sharing).
- Vídeo geral do grupo: **[INSERIR LINK DO VÍDEO GERAL AQUI]**.

## Reprodutibilidade e limitações

Ver README.md, uv.lock, configs/frozen_manifest.json e os quatro notebooks com saídas reais. Testes de software não baixam modelos e não simulam evidência de treinamento. Corpus pequeno, exemplos sintéticos e ausência de revisão humana independente limitam inferências sobre generalização. O serviço não comprova causa elétrica nem conformidade normativa e não determina prazo de reparo.

## Entregas externas pendentes

Integrantes/RMs, território/nome comercial, revisão humana dos resultados e vídeo final são itens administrativos e de validação do grupo. A disponibilidade pública e as evidências técnicas estão descritas nas seções de implantação e validação.
