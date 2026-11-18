# Auditoria dos dados e dos alvos

Revisão técnica assistida por IA em 12/11/2026. Não é adjudicação humana independente nem coleta de campo. Os alvos foram escritos com assistência de IA e revistos quanto à pergunta e ao limite da evidência; continuam sujeitos a erro de autoria e viés comum ao revisor.

| Categoria descritiva | Treino | Validação bruta | Teste bruto |
|---|---:|---:|---:|
| Observação respondível | 104 | 20 | 32 |
| Dado não consta | 64 | 16 | 20 |
| Evidência insuficiente | 88 | 16 | 20 |
| Contradição | 64 | 12 | 20 |
| Fora do escopo | 40 | 8 | 16 |
| Tentativa de indução | 40 | 8 | 12 |

Essas categorias são metadados de auditoria, não entradas da LLM. Uma tentativa de indução acompanhada de observação pode ter alvo `analise_preliminar`: categoria e status não são equivalentes. Não se transforma a presença de uma ordem em evidência de ocorrência.

Todos os alvos têm `hipoteses: []`: este ciclo ensina triagem conservadora e limites de evidência, não diagnóstico causal validado ou geração de hipóteses positivas. O contrato suporta hipóteses estruturadas, mas o benchmark não comprova essa capacidade do modelo. Os alvos usam muitas formulações padronizadas; acerto pode refletir aprendizado dessas regras e desse estilo. Não anunciar melhora geral de raciocínio a partir deste conjunto.

A cobertura em `cobertura-fontes.json` mostra que nenhum exemplo tem município informado e todos os trechos-gabarito são procedimentos autorais. A síntese da CPFL aparece em dois contextos de teste como trecho adicional; a fonte municipal da SP Regula não é recuperada sem município compatível. Assim, o benchmark não valida atendimento municipal, contratos ou conhecimento institucional amplo, apesar de essas fontes constarem da base.

**Limitação de processo:** a auditoria de cobertura executou a busca sobre entradas de teste antes da seleção dos candidatos, já com r2 em treinamento e regras congeladas. Não gerou respostas de teste, não calculou desempenho dos candidatos e não motivou ajuste de parâmetros, prompt, corpus ou escolha. Está registrada em configs/coverage_audit_deviation.json. Não apresentar o teste como dado/recuperação totalmente sem inspeção; a restrição efetivamente mantida é a abertura das respostas da LLM após seleção. A autoria/revisão comum já impede classificá-lo como validação cega independente.

São 50/20/30 famílias declaradas por divisão, com 8/4/4 variantes por família. A maioria das variantes muda apenas a formulação da pergunta; não aumenta proporcionalmente a diversidade observacional. Há campos de sensor em 32/4/12 exemplos e descrições visuais em 8/0/4. Não são imagens processadas por visão computacional nem prova de integração com sensores reais. As métricas por categoria e os intervalos por família devem acompanhar a taxa global.

## Problemas encontrados e tratamento

- Na v2, perguntas genéricas e relatos contendo pedidos ou meta-descrições permitiam alvos ambíguos. A auditoria das respostas manteve julgamentos incertos no denominador. A v3 separa pergunta e observação e não reaproveita cinco meta-descrições ambíguas de treino.
- Os alvos distinguem registrar uma observação de provar causa ou conformidade. A ausência de causa não bloqueia por si só um registro. A falta de cidade impede indicar canal municipal específico, mas não o registro genérico.
- ADC não é lux; calibração declarada não equivale a método verificado. Os campos estruturados e os alvos preservam essa distinção. Uma fotografia não identifica automaticamente uma peça defeituosa.
- Conflito exige comparar ponto, posição, condições e instante. Mudança de estado em horários diferentes não demonstra contradição por si só. A avaliação precisa conferir o significado, além do status.
- A checagem literal não encontrou duplicação exata entre divisões. A revisão semântica posterior identificou paráfrases que IDs diferentes não detectavam. O adendo anterior à geração retirou 16 casos da seleção de validação e 8 do placar confirmatório de teste, preservando e avaliando todos os casos brutos. Consulte ADENDO-AVALIACAO.md e os motivos individuais em configs/clean_holdout_plan.json.
- O conjunto confirmatório de 112 casos remove as sobreposições identificadas; não certifica independência semântica perfeita. Há conceitos e regras compartilhados entre treino e teste, corpus pequeno e autoria comum. Não interpretar resultado sintético como desempenho de campo.

## Preparação supervisionada

O contexto é a busca efetivamente executada. Não há inserção de fonte-gabarito. Citações do alvo que não foram recuperadas são retiradas e a falha é registrada: cinco exemplos de treino ficaram sem citação, nenhum da validação. Isso não muda o significado esperado nem transforma recuperação ausente em sucesso. O arquivo dados/mlx/manifest.json registra cobertura e comprimentos.

Os IDs opacos, categorias, gabaritos e divisões ficam fora do prompt de inferência. Os trechos citáveis não incluem os termos auxiliares usados no índice. Os arquivos de dados, prompt, protocolo e configurações têm hashes congelados; o adendo e a regra de seleção possuem registros separados anteriores às respostas de validação.

## Pendência

Uma pessoa do grupo precisa adjudicar dados e saídas, inclusive os casos incertos e exemplos onde a política do protótipo pode divergir do atendimento real. O caderno sintético não contém contratos, regras normativas elétricas, dados de usuários ou compromissos de operação municipal verificados. Não ampliar essas conclusões na apresentação.
