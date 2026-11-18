# Protocolo de avaliação

## Antes do placar

Os arquivos de dados e o índice são congelados por SHA em `configs/frozen_manifest.json`. O teste não participa da seleção de learning rate ou checkpoint. Não editar gabaritos após consultar o teste para anunciar melhora no mesmo placar.

O corpus é pequeno e autoral: procedimentos do protótipo e sínteses atribuídas de fontes institucionais. Não é norma elétrica. Os 600 exemplos são variantes de 72 famílias sintéticas; não equivalem a 600 observações de campo independentes. A separação é por família declarada e identidade da entrada, mas uma revisão de similaridade semântica continua importante. O objetivo inicial é testar fundamentação e formato, não certificar capacidade de diagnóstico físico.

## Treino e validação

As conversas de treino/validação de loss incluem o trecho de referência quando a busca não o recupera, com a contagem publicada em `dados/mlx/manifest.json`. É um contexto supervisionado com apoio do gabarito (oracle). Isso **não** é evidência de qualidade da recuperação. Na avaliação de geração, somente os trechos realmente recuperados são fornecidos, sem injeção do gabarito.

O MLX conta iterações por microbatch. Portanto 800 microsteps, acumulação 4 e microbatch 1 são 200 atualizações e duas passagens por 400 exemplos. A validação padrão da biblioteca ocorre antes do passo periódico; registramos o índice efetivo e avaliamos novamente os pesos finais.

Seleção técnica na validação: taxa de status esperado, JSON/referências válidos e latência. Essa seleção é um proxy automático; não representa revisão humana independente de acerto/fundamentação. A revisão manual pode exigir nova versão com identificação e protocolo próprios.

## Placar

A: base quantizada sem contexto; B: a mesma base com RAG; C: mesma base/RAG com adaptador. Mesmo esquema de saída e geração gulosa; máximo de 768 tokens. JSON bruto é preservado, sem reparo ou retry oculto.

- `status_match_rate`: igualdade do status com o gabarito **após a resposta passar pelo esquema completo**. Falhas de esquema contam como erro de status no placar, mesmo que a chave status isolada pareça correta. Referências inválidas não impedem a comparação se o esquema for válido. É uma medida de status utilizável pelo contrato, não classificação pura nem acurácia semântica integral.
- `valid_json_and_refs_rate`: esquema válido e referências pertencentes ao contexto. Não prova que a referência sustenta uma afirmação.
- Recall@k: proporção de trechos relevantes recuperados por pergunta; hit@k mede ao menos um relevante. Casos sem fonte relevante não entram no recall.
- Latência: mediana/p95 com aquecimento separado.
- Correção semântica, fidelidade, alucinação e adequação de recusa: preencher CSV de revisão por caso, com justificativa e revisor.

Uma recusa universal não é sucesso: publicar também o comportamento nos casos respondíveis. Uma citação existente pode estar mal aplicada. Menor validation loss não comprova menor alucinação.

Os cinco erros serão extraídos de falhas reais de JSON/referência ou classificação observada; causas serão hipóteses, propostas não serão declaradas como correções já validadas. Nenhum número final deve ser preenchido antes da execução correspondente.

A avaliação separa JSON sintaticamente válido, esquema válido, esquema/referências válidos e status esperado. Uma fonte inventada pode invalidar referências sem mudar a classificação de status; não misturar essas métricas. Chaves JSON duplicadas são rejeitadas.

Identificadores de ocorrência e metadados de categoria/split nunca entram no prompt. O registro original mantém IDs para auditoria, mas a LLM recebe somente a pergunta e as observações. A versão v1 com IDs foi invalidada antes do teste final; v2 é a versão científica em execução.
