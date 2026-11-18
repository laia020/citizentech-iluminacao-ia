# Ciclo v5 — Qwen2.5-1.5B treinado

Treinamento,seleção e avaliação local concluídos em17/11/2026. [Relatório](docs/RELATORIO-1_5B.md),[notebook executado](notebooks/06_treinamento_e_avaliacao_1_5b.ipynb),[placar](avaliacao/placar.json),[cinco erros](avaliacao/cinco_erros.json),[conferência final](docs/VALIDACAO-FINAL.json).

## Executar a POC existente

Para a versão atual com guarda limitada de citações, usar `scripts/servir_poc_validada.py` na raiz. O comando abaixo preserva a versão original, sem guarda, para reproduzir as evidências científicas. Equipe, URL pública do repositório, vídeo do grupo e preparação completa de novo clone estão no [README principal](../../README.md).

Na raiz `/Users/lucasmanentti/Projects/citizentech-iluminacao-ia`:

```zsh
.venv/bin/python scripts/servir_1_5b.py
```

Demo em `http://127.0.0.1:8000/demo`,API em `http://127.0.0.1:8000/docs`. Encerrar com Control+C no terminal em que iniciou. Não instalar,baixar pesos ou treinar para abrir a POC. A CLI `citizentech serve` também aponta para esta versão; comandos históricos exigem `--legacy-v2`. O serviço valida o adaptador e mantém carga/geração/liberação doMLX no mesmo worker. Não há fallback ou resposta gravada. Sem artefatos válidos retorna indisponibilidade, sem saída de modelo simulada.

## Evidências

- `configs/model.json`:Qwen2.5-1.5B, revisão989aa7980e4cf806f80c7fef2b1adb7bc71aa306,Apache-2.0; originais/FP16 em `../../models`. Procedência eSHA no modelo convertido.
- `configs/protocol.json`:configuração predefinida; seu estado de preparação é histórico, superado pela autorização registrada em `docs/autorizacao-e-recursos-treino.json`, sem mudar critérios.
- `configs/frozen_manifest.json`, `source-snapshot.json`, `codigo_congelado/`:dados,prompt e código antes do treinamento. Só a apresentação da página mudou para estado treinado; original preservado e exceção documentada na conferência. Código preditivo,dados e pesos-base preservados.
- `dados`:400 treino e80 validação herdados. `avaliacao/test.jsonl`:novo conjunto30 composicional; teste antigo120 em `regressao-conhecida.jsonl`, não executado como teste novo.
- `base/fontes.csv`:12 documentos com origem,formato,direitos e trechos; dez procedimentos autorais,duas sínteses atribuídas. Autoria/revisão de cenários relacionadas por IA, sem validação externa/humana independente; todos os alvos sem causas.
- `adapters/r1` e `r2`:400/800 passos,100/200 atualizações,8min36s/15min56s,pico12,234GB,sem swap crescente. Pesos finais exatos; r1 escolhido por validação64 antes do teste; dois orçamentos com mesma semente, não replicações independentes.
- `avaliacao/evidencias`:cópias brutas/medidas deA/B/C e validações fora de pastas ignoradas. `avaliacao/treinamento`:logs pequenos/procedências sem pesos. `avaliacao/placar.json`:métricas e revisão90 saídas.
- `revisao/valid-r1`, `valid-r2` e `test`:julgamentos explícitos,justificativas,incertos e ligaçõesSHA. Só entradas/texto/contexto exatamente idênticos reutilizaram rótulos entre validações;27 grupos,registro próprio.
- `docs/teste-poc-real.json` e `revisao-poc-conteudo.json`:seis chamadas reais,conteúdo avaliado separadamente doHTTP. `docs/VALIDACAO-PREPARACAO.json` é histórico da etapa antes do treinamento; não representa o estado final.

C no teste30:100% esquema/ref.,28/30 em status,25 acertos semânticos,3 erros,2 incertos;2 alucinações confirmadas,2 incertas. Mediana de geração1,644s e p951,798s,sem carregamento/fila/rede. A redução de alucinação frente à base tem intervalo que inclui zero; não apresentá-la como conclusiva. Ver o relatório para todas as configurações e categorias.

## Reprodução intencional

As evidências exportadas e notebook permitem estudar resultados sem carregar pesos. Para repetir inferência deliberadamente com a base/adaptador existentes, escolher nome novo:

```zsh
.venv/bin/python scripts/experimento_1_5b.py evaluate --name reproducao-C-01 --mode rag_finetuning --adapter adapters/selected/final --split test
```

Esse comando usaGPU e gera30 respostas; o teste já foi observado, portanto não é nova validação não vista. A/B usam nomes novos e modos `base_sem_contexto` / `rag_simples`,sem adaptador. Mesma política:greedy0,512 tokens,contexto2048,top3,limiar0,11 herdado da validação. Não recalibrar pelo teste.

Novo treinamento exige intenção explícita,alimentação/recursos e teste curto antes de execução longa. Os scripts recusam sobrescrever diretórios; `--execute-training` é necessário. Para reproduzir a seleção original do zero, usar uma cópia experimental separada com os dados/versões congelados e sem resultados/seleção prévios. O seletor original refere-se a r1/r2 e recusa teste já aberto; não alterá-lo para escolher outro candidato com este teste. Mudanças de dados/modelo/prompt/retrieval exigem ciclo e avaliação separados. Não prometer igualdade bit a bit em outra plataforma.

Clone novo precisa obter a revisão oficial indicada e convertê-la com MLX-LM float16. O adaptador selecionado acompanha o repositório em `../../artefatos/qwen1.5b-lora-r1.zip`; a ferramenta `scripts/preparar_runtime.py`, na raiz, verifica o pacote e o restaura sem substituir adaptadores diferentes. Seguir o [guia completo da raiz](../../README.md) para preparar base, vínculo e adaptador. Pesos-base e diretórios de execução permanecem ignorados pelo Git. Comando de conversão de referência, somente com destino inexistente:

```zsh
.venv/bin/python -m mlx_lm convert --hf-path models/qwen-1.5b-original --mlx-path models/qwen-1.5b-fp16 --dtype float16
```

O lockfile e procedência registram versões; não atualizar bibliotecas por conveniência. O clone público limpo e a implantação externa não foram executados nesta tarefa. Scripts de notebook,exportação e conferência consomem artefatos existentes e recusam colisões; não repeti-los sobre resultados sem preservar cópia/novo destino.

## Limites e restauração

Na execução original foram aprovados 39 testes; a revisão documental/runtime e a guarda ampliaram a suíte para 47 testes aprovados. Análise estática, congelamentos/hash e notebook verificados; nenhuma biblioteca instalada/atualizada. Equipe informada e publicação do repositório autorizada. Revisão humana independente, integração real do grupo, link do vídeo, disponibilidade pública da API e inspeção visual continuam pendentes. A publicação do código não inclui deploy nem mudança global do Mac/Codex.

Backup desta etapa:`/Users/lucasmanentti/.codex/backups/citizentech-treino-1_5b-20261117-204424`,com manifesto de documentos/configurações/notas. Restaurar por comparação/cópia do arquivo desejado, preservando alterações posteriores. Não apagar dados,ambientes ou pesos para restaurar documentação. Os artefatos500M removidos por autorização anterior não voltam por esse backup documental. Outras versões permanecem históricas,sem reutilizar seus resultados como métricas1.5B.
