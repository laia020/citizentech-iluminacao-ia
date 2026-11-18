# Eventos de execução

## Testes antes do código

Os testes principais foram escritos antes dos módulos de implementação. A execução inicial (`docs/tdd-red.txt`) falhou por ausência dos módulos. Após implementação, a suíte passou; verificações adicionais importantes de contrato/revisão foram acrescentadas depois. O total atual e a saída estão em `docs/testes-principais.txt`.

## Treinamento e repouso automático

No início do primeiro candidato houve períodos de repouso do macOS, identificados no registro de energia. A duração wall-clock do candidato inclui essas interrupções e não deve ser usada sozinha para estimar throughput contínuo da máquina. Uma prevenção temporária de repouso foi associada ao processo dos experimentos, sem alterar configurações permanentes ou proteção térmica. Deve ser liberada ao encerrar o processo e antes do repouso final solicitado pelo usuário.

## Verificação visual

A abertura de `http://127.0.0.1:8000/demo` pelo navegador foi rejeitada pelo controle de aprovação, indicando permissão recusada. Não houve tentativa de contorno por outro navegador ou ferramenta de captura. A verificação visual permanece pendente; testes automatizados verificam disponibilidade do HTML e contrato. O servidor temporário usado nessa tentativa foi encerrado.

## Rastreabilidade dos dados e implementação

Os primeiros exemplos e conversas de teste curto foram preservados em `runs/draft-dados-inicial` e `runs/draft-mlx-smoke` antes do congelamento dos candidatos oficiais. A contagem de tokens foi corrigida para usar explicitamente `return_dict=False` do tokenizer; os conjuntos oficiais foram medidos sem truncamento antes dos candidatos. O maior exemplo ficou abaixo de 2.048 tokens.

Após o congelamento, o teste, corpus, limiar e dados oficiais são verificados por hash. Ajustes posteriores de formatação, validação de artefatos, contrato OpenAPI e agregação de revisão não alteraram pesos base, dados ou parâmetros de treinamento. Versões, configurações, revisões e hashes relevantes ficam nos manifestos dos runs e em configs/model.json.

## Limites de conclusão

Resultados automáticos de formato/status não são revisão humana independente de acerto ou alucinação. Não foram feitos commits, pushes, publicação, contratação de hospedagem ou exposição externa do Mac.

## Correção de vazamento de rótulo — versão de prompt v2

Foi detectado que ocorrencia_id incluía categoria/split nos dados sintéticos e estava sendo enviado ao modelo. O teste de regressão falhou antes da correção. O identificador foi removido da entrada da LLM (permanece somente no envelope controlado pela API). As conversas foram reconstruídas, medidas em tokens e congeladas novamente. Rodadas anteriores foram preservadas em runs/invalid-label-leak-20261112-033851 e excluídas da seleção e do placar. Nenhum teste final A/B/C havia sido executado antes da correção. Os dois candidatos serão repetidos na versão v2; os números anteriores não comprovam melhoria científica.

## Conferências adicionais de integridade

O guardião de congelamento foi ampliado para conferir também o hash do prompt de sistema, sem mudar seu conteúdo, dados ou parâmetros dos candidatos. O teste falhou antes da correção (docs/tdd-congelamento-red.txt) e a suíte passou depois. A auditoria textual descritiva entre splits está em docs/auditoria-similaridade.json; ela não foi usada para alterar exemplos, gabaritos, limiar ou seleção. Os registros pequenos dos treinos concluídos serão copiados para avaliacao/treinamento, separadamente dos pesos locais, pela conferência final.

A conferência de congelamento também passou a verificar os arquivos originais listados no manifesto de dados já congelado. A falha foi reproduzida antes da correção em docs/tdd-dados-originais-red.txt. Os arquivos originais foram conferidos e continuam idênticos aos hashes registrados; não houve mudança de dados, prompt ou hiperparâmetros.

A documentação da métrica status_match foi explicitada conforme o código que já estava em execução: comparação somente após validação do esquema, com referências pontuadas separadamente. A lógica, os resultados e o critério de seleção não foram alterados após consultar o teste; essa métrica não é classificação pura nem acurácia semântica.

## Correção da API com MLX real

O teste ASGI com pesos reais encontrou RuntimeError de stream CPU criado em outro thread, apesar dos testes com gerador falso. A falha inicial foi preservada em runs/validacao-api-real-falha-thread.json e runs/diagnostico-api-thread.log. O serviço agora carrega, executa e libera o modelo em um único worker dedicado, mantendo health/ready responsivos e uma inferência por vez. Um teste de regressão verifica afinidade do worker e encerramento (falha anterior em docs/tdd-api-worker-red.txt); a suíte passou com 25 testes. O transporte foi repetido com sucesso, sem mudar pesos, prompts, dados, limiar ou placar A/B/C. O carregamento/generação offline do experimento não foi alterado. Referência primária de contexto: https://github.com/ml-explore/mlx/issues/3727 ; implementação da versão instalada inspecionada localmente. HTTP 200 não será apresentado como acerto semântico; respostas inadequadas permanecem registradas.
