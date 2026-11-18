# Estado de aceitação local — 12/11/2026

**Implementação e experimentos locais concluídos. Metas de qualidade ainda não atingidas; revisão e integração externa pendentes.** Este registro não declara a GS integralmente entregue nem o modelo pronto para decisões autônomas.

| Requisito | Evidência real | Estado / limite |
|---|---|---|
| AC-01 — tarefa e teste | SPEC, 400 treino / 80 validação / 120 teste, manifestos | Congelados; 72 famílias sintéticas; revisão independente dos alvos pendente |
| AC-02 — fontes e trechos | base/catalogo.jsonl, chunks.jsonl, fontes.csv, docs/FONTES.md | 12 documentos/trechos; materiais autorais e sínteses atribuídas; publicação exige revisão do titular |
| AC-03 — recuperação | configs/retrieval.json, notebook 02, placar | Limiar só na validação; recall@1=72,5%, recall@3=82,5% nos respondíveis do teste; meta de 90% não atingida |
| AC-04 — JSON, fontes e recusa | 360 saídas brutas, validação estrita e CSVs de revisão | C: sintaxe 98,3%, esquema/referências 93,3%; meta de esquema de 95% não atingida; revisão semântica pendente |
| AC-05 — especialização | Dois candidatos de 800 microsteps/200 atualizações, adaptadores salvos/recarregados | Treino real local em MLX; 2,884 milhões de parâmetros treináveis; selecionado lr1e5 na validação |
| AC-06 — comparação | avaliacao/placar.json, respostas/, notebook 04, INTERPRETACAO.md | A/B/C completos nos mesmos 120 casos; ganhos globais e regressões por categoria documentados |
| AC-07 — cinco erros | avaliacao/cinco_erros.json e docs/CINCO_ERROS.md | Cinco falhas reais de famílias diferentes; seleção concentrada em respondíveis, sem representar todos os tipos de erro |
| AC-08 — reprodução | README, uv.lock, scripts, quatro notebooks com saídas | Validado neste Mac; testes não baixam modelos; pesos locais preservados e não publicados |
| AC-09 — API | OpenAPI, cliente, demo, docs/validacao-api-real.json | 5 casos ASGI com modelo real, health/ready e HTTP 200; integração real do grupo pendente; verificação visual bloqueada por permissão |
| AC-10 — relatório e publicação | Relatório, roteiro e notebooks | Integrantes/RMs, vídeo gravado, revisão final, repo/MVP público e autorizações de publicação pendentes |

## Software e execução real

25 testes principais/regressões aprovados em docs/testes-principais.txt, com falhas anteriores preservadas nos arquivos tdd-*. O serviço foi corrigido após um erro real de afinidade de stream do MLX: criação, inferência e liberação agora ficam no mesmo worker. O teste de regressão e os cinco casos com o modelo real passaram pelo transporte e esquema. Nenhum peso ou parâmetro do experimento foi modificado para corrigir a API.

No teste operacional da API, registro_minimo retornou analise_preliminar e o sensor ADC sem calibração retornou informacao_insuficiente. Entretanto, a ocorrência com causa não inspecionada foi excessivamente recusada; “não consta” recebeu justificativa inadequada e o conflito explícito recebeu analise_preliminar. Essas falhas de conteúdo permanecem registradas. **5/5 HTTP 200 não significa 5/5 análises corretas.** Não houve avaliação humana independente desses casos.

A conferência final de hashes, cobertura, contexto B/C e adaptador está em docs/validacao-entrega.json. Os notebooks leem artefatos reais e não iniciam treinamento automaticamente. Não foram executados commits, pushes, publicação, abertura externa de portas ou mudança permanente de energia/proteções do macOS.

## Pendências para a entrega do grupo

Revisar os alvos e as 360 respostas com identificação do revisor; decidir novo ciclo para atingir as metas de qualidade e tratar regressões; conectar o consumidor real dos colegas; preencher integrantes/RMs e território; definir publicação/infraestrutura e direitos; gravar vídeo e conferir links após autorização. O roteiro entregue é um guia, não um vídeo gravado.

A abertura da página local no navegador foi recusada pelo controle de aprovação por falta de permissão. Não houve contorno por outra ferramenta. A disponibilidade do HTML, sintaxe JavaScript e contrato foram conferidos, mas layout/interação visual continuam pendentes.

O encerramento salva todos os artefatos e interrompe apenas recursos desta execução. O Mac será colocado em repouso conforme solicitado; a API local não ficará disponível durante o repouso. A solicitação de repouso não equivale a verificação independente de que o computador já esteja dormindo.
