# Interpretação dos experimentos v2

## O que foi medido

Foram concluídos dois candidatos QLoRA de 800 microsteps/200 atualizações cada, selecionados por 80 casos de validação. O teste congelado tem 120 variantes de 24 famílias sintéticas; foram geradas 360 respostas A/B/C. Não são 360 observações de campo independentes.

| Medida no teste | A: sem contexto | B: RAG simples | C: RAG + fine-tuning |
|---|---:|---:|---:|
| Sintaxe JSON | 120/120 (100%) | 120/120 (100%) | 118/120 (98,3%) |
| Esquema completo | 55/120 (45,8%) | 92/120 (76,7%) | 112/120 (93,3%) |
| Esquema e referências | 55/120 (45,8%) | 89/120 (74,2%) | 112/120 (93,3%) |
| Status esperado após esquema válido | 28/120 (23,3%) | 59/120 (49,2%) | 78/120 (65,0%) |
| Status esperado nos respondíveis | 8/40 (20,0%) | 20/40 (50,0%) | 30/40 (75,0%) |
| Mediana da geração, segundos | 2,54 | 3,01 | 2,47 |
| p95, segundos | 3,59 | 4,10 | 2,79 |

`status_match_rate` exige esquema válido, mas não exige referências válidas. Portanto é uma medida de status utilizável pelo contrato, não classificação pura. Parte da melhora pode decorrer do formato mais consistente. Nenhuma taxa acima representa acurácia semântica ou taxa de alucinação.

## A × B: contexto

Neste conjunto, acrescentar os trechos aumentou o atendimento ao esquema e o status esperado. Ainda há falhas: no caso test-respondivel-01-v01, B recebe registro:1 e mesmo assim diz que luminária acesa à tarde pode ser normal, enquanto a fonte autoral orienta registrar a observação. Ter uma citação existente não prova fidelidade.

## B × C: especialização

C produziu 23 respostas adicionais com esquema/referências válidos e 19 adicionais com status válido esperado em 120 casos. A mediana foi menor, mas as respostas de C são mais padronizadas; não se pode atribuir isso a uma melhora geral de raciocínio ou throughput. O maior resultado global não é uniforme:

| Categoria | B: status válido esperado | C: status válido esperado |
|---|---:|---:|
| Respondível | 20/40 | 30/40 |
| Não consta | 2/20 | 8/20 |
| Insuficiente | 13/20 | 19/20 |
| Contradição | 11/15 | 7/15 |
| Fora do escopo | 6/15 | 9/15 |
| Indução | 7/10 | 5/10 |

C regrediu em contradição e indução. Não declarar menor alucinação: revisão humana independente das afirmações e fontes está pendente. O protótipo organiza encaminhamento humano; não certifica diagnóstico elétrico nem deve automatizar manutenção.

## Recuperação e metas que não foram atingidas

B e C usam o mesmo recuperador e os mesmos contextos. Nos 40 casos respondíveis, recall@1=72,5% e recall@3=82,5%. **A meta de recall@3 de pelo menos 90% não foi atingida.** A validação respondível tinha recall@3 de 100%; a queda no teste ilustra a limitação da busca lexical em novos cenários. Exemplo concreto: “suporte luminoso aparentemente danificado” não recebe contexto em test-respondivel-03-v01.

O limiar 0,16 foi escolhido somente na validação, com uma aproximação binária de respondibilidade: TP=20, FP=44, FN=0, F1≈0,476. Esse critério tem muitos falsos positivos e não é detector confiável de respondibilidade. Não foi recalibrado com o teste.

A SPEC define JSON válido por parsing **e conformidade do esquema**. A meta de pelo menos 95% também **não foi atingida por C: 93,3%**. Seus 98,3% de sintaxe, isoladamente, não bastam. O resultado foi preservado, sem reparo oculto, retry ou troca posterior de adaptador.

## Seleção e limites

O candidato lr1e5 obteve 57/80 status válidos esperados, contra 56/80 do lr5e5, e foi escolhido pelo critério previamente implementado que prioriza status. O lr5e5 teve melhor esquema/referências (79/80 contra 75/80) e menor validation loss. A diferença de um caso em poucas famílias não sustenta superioridade estatística; menor loss não foi usada como prova de melhor resposta.

Contextos supervisionados incluíram apoio-gabarito em 225 casos de treino e 40 de validação de loss. Isso não ocorreu na geração de validação/teste. As rodadas v1 que recebiam IDs informativos foram invalidadas, arquivadas e repetidas antes do teste final. V2 exclui IDs e metadados da entrada da LLM. A revisão humana independente de alvos e resultados continua necessária.

## Próximo ciclo proposto, não executado

Revisar ambiguidades dos alvos com o grupo; ampliar cenários independentes, conflitos, indução e casos sem contexto; melhorar a cobertura de sinônimos da recuperação e a validação de formato. Fazer essas alterações em uma nova versão, com novo conjunto final não visto, preservando este placar. Não corrigir exemplos ou limiar a partir deste teste e anunciar o mesmo teste como novo.

As respostas completas, prompts e contextos estão em avaliacao/respostas/. Cinco falhas rastreáveis e propostas estão em avaliacao/cinco_erros.json e docs/CINCO_ERROS.md. Julgamentos semânticos e integração externa permanecem pendentes.

## Verificação operacional da API

Após corrigir a afinidade de thread do MLX, cinco casos simulados receberam HTTP 200. O registro mínimo foi analisado e o sensor sem calibração foi recusado adequadamente no aspecto observado. Ainda há falhas: a formulação com causa não inspecionada foi excessivamente recusada; o pedido de custo/prazo recebeu justificativa sem pertinência (inclusive a expressão inadequada “calibração da causa elétrica”); o conflito explícito foi classificado como análise preliminar. O relatório bruto foi preservado. Esses casos demonstram por que esquema e fontes existentes não bastam para validar o conteúdo. Não foram usados para trocar o adaptador ou reescrever o placar.
