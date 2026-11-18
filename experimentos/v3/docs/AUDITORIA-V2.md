# Auditoria técnica das respostas v2

**Revisão técnica assistida por IA; não é revisão humana independente.** Foram examinadas as 360 respostas: 293 grupos de saída textual idêntica, da mesma família e com os mesmos trechos recebidos. Todas as perguntas de cada grupo foram mostradas ao revisor. Nenhum rótulo A/B/C foi mostrado nos pacotes de anotação; estilos de resposta ainda podem permitir inferências, portanto isso não garante cegamento perfeito.

| Modo | Acerto semântico: limite inferior–superior | Acerto integral: limite inferior–superior | Afirmações sem apoio |
|---|---:|---:|---:|
| final-A | 34.2%–50.0% (19 incertos) | 19.2%–20.8% | 6/120 (5.0%) |
| final-B | 48.3%–64.2% (19 incertos) | 37.5%–40.0% | 13/120 (10.8%) |
| final-C | 55.8%–68.3% (15 incertos) | 53.3%–63.3% | 4/120 (3.3%) |

Limites incluem os casos incertos no denominador: não se remove uma ambiguidade para melhorar o resultado. Acerto integral exige esquema e referências válidos, conteúdo correto, fundamentação e enquadramento adequado, sem alucinação anotada. Semântica é medida separadamente do formato. Recusa inadequada no relatório inclui enquadramento de status incompatível com a política, não significa automaticamente obediência a uma instrução maliciosa.

## O que é sustentado pelos dados desta revisão

Houve mais acertos integrais e menos afirmações sem apoio em C que em A e B neste conjunto, segundo os critérios da revisão técnica por IA. Isso não equivale a validação humana, generalização para campo ou ausência de alucinação. A redução de 6 para 4 casos em relação a A é pequena. O intervalo pareado por família para essa redução inclui zero; a evidência estatística não permite afirmar uma redução robusta em relação ao modelo sem contexto. A comparação C × B teve diferença maior, mas continua condicionada à qualidade dos julgamentos por IA.

Os intervalos por bootstrap são condicionais a estas anotações e a famílias sintéticas declaradas. Eles não medem erro do revisor, viés de autoria dos dados, nem representatividade no mundo real. Os alvos também foram construídos com assistência de IA.

## Exemplos verificáveis

- Sem contexto: uma resposta escreveu LDR como Lucas de Referência. A expansão não consta da entrada nem das fontes.
- Algumas respostas atribuíram defeito de rede ou regulagem de transformador sem medição e com fontes que só orientavam registro.
- Algumas respostas transformaram sensor não especificado em LDR/ADC, copiando características gerais do documento para o caso.
- Houve também erros do modo especializado: afirmar existir observação de iluminação quando a entrada só tinha uma ordem, ou declarar falta de calibração quando ela foi informada.
- Nos conflitos, houve inversão literal: dois relatos discordavam do estado no mesmo instante, mas uma saída disse que concordavam no estado e divergiam no horário.

## Correções derivadas da revisão

A v3 separa pergunta e observação, retira meta-descrições ambíguas, inclui exemplos estruturados e preserva alvos pertinentes. O índice inclui vocabulário de domínio sem expor termos auxiliares como documento citável. A calibração usa relevância dos trechos, não respondibilidade aproximada. O treino não insere fonte-gabarito. As regras do prompt explicitam limites de calibração, evidência e conflito.

Os arquivos mapping.json, decisions.jsonl e reviewed_responses.jsonl contêm entrada, resposta bruta, fontes recebidas e justificativa por resposta. A consolidação foi ligada aos arquivos originais por igualdade textual/contexto e SHA. O antigo placar estrutural não foi substituído por estas anotações. A v2 é regressão histórica conhecida para o novo desenvolvimento, não teste novo não visto.

A comparação de semântica isolada C × A também tem intervalo que inclui zero. O ganho de acerto integral não deve ser anunciado como prova isolada de melhora de raciocínio ou conteúdo, pois inclui formato. A demonstração histórica mostra um caso favorável e uma falha do próprio modo especializado, com saídas brutas, em DEMONSTRACAO-HISTORICA.md.
