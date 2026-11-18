# Revisão e experimento v3

O protocolo completo está em configs/protocol.json. Dados, prompt e configuração foram congelados antes do treino e do teste final. O código da rodada foi copiado para codigo_congelado/. A v2 permanece nos caminhos originais e no backup indicado em configs/backup.json.

Os 600 exemplos são variantes de 100 famílias sintéticas declaradas; não são 600 ocorrências independentes. O novo teste tem 120 variantes de 30 famílias e não participa de escolhas de modelo/parâmetros. A v2 passa a ser regressão histórica conhecida.

Foram removidas cinco descrições ambíguas de pedido/registro do caderno de treino antigo, separadas perguntas e observações e acrescentados dados estruturados. Os alvos preservam o significado do pedido. Na preparação supervisionada, as citações são limitadas aos trechos realmente recuperados: não se insere fonte-gabarito. Falhas de recuperação são registradas.

A busca inclui vocabulário de domínio no índice, separado dos trechos citáveis, e pondera a pergunta específica. O limiar foi calibrado por relevância de documentos na validação, não por uma aproximação de respondibilidade. Todos os modos usam o mesmo prompt claro, geração gulosa, orçamento, validação estrita e nenhuma correção oculta. B e C recebem os mesmos contextos.

O primeiro candidato usa lr=1e-5 e 800 microsteps. Um segundo lr=5e-5 é permitido somente por desempenho insuficiente na validação conforme o protocolo; nenhum resultado de teste decide novo treino.

A revisão de significado e afirmações será técnica por IA, apoiada por verificações explícitas e justificativas por caso. Não se identifica o agente como humano, não se preenchem os CSVs antigos de revisão humana e não se promete revisão independente. A demonstração será rotulada com esse limite. Se não houver evidência de mais acertos e menos alucinação, a conclusão não será fabricada.
