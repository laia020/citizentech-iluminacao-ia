# Interrupção numérica e repetição estabilizada

A execução original r2, com taxa 5e-5, foi interrompida quando o relatório do passo 240 apresentou loss não finita. O primeiro microbatch afetado não foi isolado: o intervalo de relatório é de 20 passos. O último checkpoint salvo, passo 200, foi verificado como finito. Essa rodada é incompleta, não elegível e não equivale a 800 passos. Seus arquivos e log foram preservados.

Não houve erro de falta de memória no registro: o último relatório finito tinha cerca de 30 GB disponíveis e zero crescimento de swap. Isso não identifica a operação matemática exata que originou o NaN. O erro não foi atribuído a temperatura ou defeito do Mac.

## Inspeção da implementação

O trainer instalado aplica gradientes sem verificá-los antes da atualização. A checagem anterior do projeto observava a loss no relatório; ela interrompe o treino, mas pode detectar o problema depois que os pesos em memória já foram contaminados. Há relato primário desse risco no repositório do MLX-LM, inclusive de que clipping sozinho não corrige NaN/Inf. Isso motiva uma proteção, sem provar que a causa específica é a mesma neste caso: [issue 1658](https://github.com/ml-explore/mlx-lm/issues/1658). Um mantenedor também explica a dificuldade de localizar essas operações: [discussão 636](https://github.com/ml-explore/mlx-lm/discussions/636).

A inspeção local encontrou ainda um problema de reprodução: `train_model` controla a semente do MLX, mas a inicialização NumPy do fluxo principal não era executada pelo wrapper direto. Portanto, r1 e r2 anteriores têm semente MLX 42, mas a ordem dos exemplos não foi completamente controlada. Não anunciar reprodução exata dessas ordens ou comparação isolada de taxas de aprendizado.

## Rotina local nova

A biblioteca instalada e o código congelado da execução original não foram alterados. A repetição r2s usa uma rotina local separada, com:

- conversão apenas em memória dos parâmetros e escalas flutuantes para FP32; códigos quantizados de 4 bits e arquivos-base preservados;
- semente 42 explicitamente no NumPy e no MLX;
- verificação da loss e de cada gradiente antes de qualquer atualização;
- acumulação de quatro microbatches e limitação da norma do gradiente médio em 1;
- parada se houver valor não finito; nenhum lote ou atualização é silenciosamente pulado;
- mesmas 800 microetapas, 200 atualizações, dados, LoRA rank16 q/v nas últimas16 camadas, taxa5e-5 e regras de inferência;
- validação de loss após cada100 passos e no final exato, sem gradiente; uso dos pesos finais para seleção;
- novo diretório e proveniência, preservando os checkpoints incompletos e sem fingir retomada sem estado de otimizador.

O fluxo difere de r1 também em precisão, proteção, controle da ordem e agendamento diagnóstico da validação. A seleção compara pipelines completos. A comparação final A/B/C mantém a mesma inferência, base, prompt e contexto, mudando apenas a disponibilidade de contexto e a presença do adaptador conforme o modo. Não inferir causalidade exclusiva da taxa de aprendizado entre candidatos.

Três testes escritos antes da implementação verificam clipping finito e bloqueio de NaN/Inf sem mudar pesos ou otimizador. O teste real curto de16 passos/4 atualizações concluiu com pico MLX de15,17 GB, sem crescimento de swap e pesos alterados. O adaptador curto foi recarregado com a base de inferência FP16; isso verifica compatibilidade, não qualidade final. A execução completa e sua validação ainda precisam terminar.

O adendo foi registrado antes de qualquer resposta de teste da LLM em `configs/stabilization_amendment.json`. A regra em `configs/stable_selection_rule.json` preserva a ordem de critérios nos64 casos de validação e permite a repetição completa r2s no lugar da r2 incompleta. A inspeção anterior da cobertura de recuperação do teste permanece declarada em `configs/coverage_audit_deviation.json`.
