# Cinco erros reais

Selecionados automaticamente entre falhas observadas, alternando modos e evitando repetir a mesma família. Todos os cinco selecionados são respondíveis; eles não representam a distribuição completa dos erros. O placar por categoria e as 360 respostas brutas permitem examinar as demais falhas. Esta análise técnica do agente não substitui revisão humana independente.

| Caso / run | Observação verificável | Hipótese de causa e proposta para novo ciclo |
|---|---|---|
| test-respondivel-00-v01 / final-A | Ponto apagado à noite foi classificado como informação insuficiente; a tarefa permite registrar a observação sem determinar causa. Não havia contexto em A. | Possível confusão entre triagem e diagnóstico. Contrastar essas duas tarefas em novos exemplos, mantendo este teste preservado. |
| test-respondivel-01-v01 / final-B | A resposta diz que luz acesa à tarde pode ser normal e recusa a análise, apesar de registro:1 orientar registrar a observação diurna. | Uso insuficiente do trecho recuperado. Rever fidelidade e exemplos contrastivos; uma citação existente não resolve essa falha. |
| test-respondivel-03-v01 / final-C | “Suporte luminoso aparentemente danificado” não recuperou contexto e foi recusado. O gabarito permite registro preliminar. | A ausência de trechos é verificável; a explicação lexical é uma hipótese. Ampliar cobertura de linguagem e medir recall em nova versão, sem baixar o limiar com base neste caso. |
| test-respondivel-02-v01 / final-A | Intermitência em travessia pública foi recusada por falta de detalhes, embora já haja observação registrável. | Possível exigência de evidência de causa para uma tarefa de registro. Novos cenários devem distinguir o que pode ser registrado do que permanece desconhecido. |
| test-respondivel-04-v01 / final-B | A resposta encaminha o registro de feixe obstruído, mas marca informação insuficiente por não concluir causa elétrica. | Há incoerência entre encaminhamento e status esperado. Rever definição de status e avaliar exemplos contrastivos em nova versão. |

As entradas, respostas brutas, alvos, trechos recuperados e identificadores completos estão em avaliacao/cinco_erros.json. Nenhuma proposta acima foi apresentada como correção já implementada ou validada. O gabarito completo descreve o comportamento desejado com fonte; A deliberadamente não recebe essa fonte, e sua avaliação de status permite usar a observação sem citar documento ausente.
