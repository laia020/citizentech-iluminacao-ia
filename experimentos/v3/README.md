> **Histórico7B encerrado:** r1 concluiu, r2 apresentou NaN e r2s foi interrompida após checkpoint200 por mudança de modelo solicitada pelo usuário. Não há seleção final v3 ou testeA/B/C novo concluído nessa pasta. Os textos de execução abaixo são históricos. A versão atual é [v5-1.5b](../v5-1.5b/README.md), preparada e ainda sem treinamento. Não reiniciar este ciclo histórico por iniciativa própria.

# Revisão v3 — CitizenTech Iluminação IA

Raiz do projeto: `/Users/lucasmanentti/Projects/citizentech-iluminacao-ia`.

Esta revisão está em execução. R1 concluiu; a tentativa r2 apresentou NaN e foi preservada como incompleta. A repetição estabilizada r2s está em treinamento, após teste curto real e recarga compatível do adaptador. Resultados finais só serão declarados após conclusão das execuções e revisão das respostas. A v2 e seus resultados originais foram preservados; a revisão técnica de suas 360 respostas está em `docs/AUDITORIA-V2.md`.

## Evidências e decisões

- `docs/AUDITORIA-DADOS.md`: dados, alvos, limitações e sobreposições.
- `docs/FONTES-REVISAO.md` e `base/fontes.csv`: fontes, abrangência e direitos.
- `configs/protocol.json`: protocolo original congelado.
- `docs/ADENDO-AVALIACAO.md`, `configs/clean_holdout_plan.json` e seu hash: subconjuntos fixados antes da geração e uso dos pesos finais de 800 passos.
- `configs/selection_rule.json`: ordem dos critérios, anterior às respostas de validação.
- `docs/ESTABILIZACAO.md`, `configs/stabilization_amendment.json` e `configs/stable_selection_rule.json`: falha numérica, controle incompleto da semente antiga, proteção/precisão novas e elegibilidade de r2s. A ordem de critérios de seleção foi preservada.
- `configs/coverage_audit_deviation.json`: a auditoria de fontes incluiu recuperação do teste antes da seleção, sem gerar respostas de teste ou usá-la para ajustar candidatos; não apresentar esse material como totalmente sem inspeção ou validação cega independente.
- `configs/frozen_manifest.json` e `codigo_congelado/`: dados, política e código da rodada.
- `adapters/r*/provenance.json`, `metrics.jsonl`, `summary.json`: parâmetros, recursos e comprovação do treinamento.
- `runs/valid-r*/`: seleção pela validação; `runs/final-A`, `final-B`, `final-C`: respostas brutas e métricas finais, quando concluídas.
- `revisao/v2` e `revisao/v3`: julgamentos técnicos por IA, justificativas, dados de ligação e incertezas; não são revisão humana independente.

O conjunto bruto contém 400/80/120 exemplos de treino/validação/teste. O adendo define 64 casos para seleção e 112 para comparação confirmatória após retirar paráfrases identificadas. Todos os 80/120 casos brutos são gerados e preservados. As variantes são correlacionadas e sintéticas; não se afirma independência semântica perfeita ou desempenho de campo.

## Comandos locais explícitos

Executar no diretório raiz com a `.venv` existente. Não instalar, baixar pesos ou treinar novamente apenas para abrir o serviço. Não usar o comando antigo `citizentech serve` esperando carregar a v3: ele preserva a v2.

Após existir `configs/selected.json`, o serviço revisado pode ser aberto com:

```sh
.venv/bin/python scripts/servir_v3.py
```

A API fica apenas em `127.0.0.1:8000`; a demonstração fica em `http://127.0.0.1:8000/demo`. O formulário revisado separa pergunta e observação e mostra uma leitura simples do resultado, com resposta completa disponível para conferência. O serviço verifica o hash do adaptador selecionado e mantém carregamento e geração do MLX no mesmo worker. Para encerrar, usar Ctrl+C. O modelo não inicia treinamento, não realiza reparos e não abre protocolo externo.

Para repetir inferência intencionalmente, escolher um nome de execução novo, pois resultados existentes não são sobrescritos:

```sh
.venv/bin/python scripts/experimento_v3.py evaluate --name reproducao-C-01 --mode rag_finetuning --adapter adapters/selected/final --split test
```

Esse comando executa 120 inferências e usa a GPU. A avaliação de teste só é liberada após seleção registrada. Não escolher novos parâmetros com os resultados de teste nem chamá-los de teste não visto depois de usados para desenvolver alterações.

O treinamento é uma ação separada e custosa. Para reprodução intencional, usar os dados congelados e registrar novo nome; a configuração da primeira rodada é:

```sh
.venv/bin/python scripts/experimento_v3.py train --name reproducao-r1-01 --lr 0.00001 --microsteps 800
```

O segundo candidato é condicional, conforme o protocolo/adendo; não há requisito de repetir o fine-tuning um número fixo de vezes. Preservar resultados históricos, verificar alimentação, memória e espaço antes de uma reprodução longa. O snapshot registra versões efetivamente utilizadas; não atualizar bibliotecas para reproduzir por conveniência.

A tentativa r2 original falhou; não usar seus arquivos parciais como modelo de 800 passos. Para reproduzir intencionalmente o pipeline estabilizado, com novo nome, o comando é:

```sh
.venv/bin/python scripts/treinar_estavel_v3.py --name reproducao-r2s-01 --lr 0.00005 --microsteps 800
```

Ele usa FP32 em memória, norma máxima de gradiente1, verificação antes de atualizar e sementes NumPy/MLX42. Não é uma comparação isolada de taxas de aprendizado contra r1. Os códigos quantizados e arquivos-base ficam intactos. Consultar `docs/ESTABILIZACAO.md` antes de escolher qual procedimento reproduzir.

## Limites da entrega

Revisão independente pelo grupo, dados de integrantes/RMs, consumidor integrado real, publicação autorizada e vídeo continuam pendentes. HTTP 200 e JSON válido não provam conteúdo correto. A inspeção visual da interface local não foi realizada: a tentativa anterior foi recusada pelo controle automático de aprovação. Essa restrição não foi contornada por outro meio.

## Preservação

Backup anterior à revisão: `/Users/lucasmanentti/.codex/backups/citizentech-revisao-v3-20261112-110809`. `configs/backup.json` registra a origem. Os pesos-base e a `.venv` foram reutilizados; adaptadores novos ficam nesta pasta, separados da seleção v2. Restaurar um arquivo exige comparar a cópia do backup com a versão atual e copiar apenas o arquivo desejado de volta, preservando alterações posteriores. Não é necessário apagar dados, ambientes ou pesos para restaurar documentação.
