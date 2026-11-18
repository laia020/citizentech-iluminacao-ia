# Migração para nuvem — 18/11/2026

Requisito explícito: interface, API e inferência precisam funcionar com o Mac desligado. O serviço local anterior foi encerrado. O usuário solicitou a preparação/publicação da versão em nuvem e autenticou a conta Hugging Face pelo fluxo oficial no navegador.

## Estado

Space publicado e em execução em [laia020/citizentech-iluminacao-ia](https://huggingface.co/spaces/laia020/citizentech-iluminacao-ia), hardware gratuito `zero-a10g`. [Abrir a tela](https://laia020-citizentech-iluminacao-ia.hf.space/demo). Duas chamadas públicas conhecidas responderam HTTP200 com triagem pertinente e recusa por dado ausente. A inferência é independente do Mac. Estado e controles em `docs/VALIDACAO-NUVEM.json`.

O ambiente foi alinhado às exigências do builder: `spaces==0.51.3` e extras `gradio[oauth,mcp]`, que limitam Pydantic a 2.12.5. A montagem FastAPI também exigiu chamar o hook de inicialização ZeroGPU que normalmente é chamado por `Blocks.launch`. Falhas iniciais e commits de publicação permanecem registrados. Não houve mudança de modelo, pesos, prompt, dados ou placar histórico.

## Implementação

- Backend PyTorch separado em `src/citizentech_ia/cloud/`, sem importar MLX na nuvem.
- Os tensores F32 e escala do adaptador r1 original são lidos diretamente do ZIP verificado; não houve fusão, quantização ou novo treinamento.
- Mesma busca, limiar, prompt, contexto e limite de geração v5; validações e guarda limitada preservadas no endpoint de GPU.
- A ponte HTTP preserva `/v1/analisar` e encaminha ao endpoint Gradio na própria instância. Falha da GPU/cota retorna erro explícito, sem geração no Mac ou resposta gravada.
- A interface mantém o visual Akona e os cinco cenários fictícios; somente indicações de execução local são ajustadas na cópia de nuvem.
- Entradas marcadas como não simuladas são recusadas; `simulada` precisa ser verdadeiro, tanto na rota HTTP quanto na fila. Essa declaração não detecta automaticamente se um visitante inseriu dados reais indevidamente.

## Validações realizadas

- Cinco testes principais escritos antes da implementação da migração; execução inicial acusou o módulo ainda inexistente. Depois passaram.
- Backend matemático: 32 módulos reais comparados com a implementação MLX original, em um ensaio restrito de LoRA F16 com base zerada; maior diferença absoluta 0,0001220703125, dentro da tolerância registrada. `docs/paridade-lora.json`.
- Qwen1.5B real em CPU PyTorch, base oficial já existente, adaptador original: um caso conhecido da POC retornou HTTP200, JSON e fontes válidos, com triagem pertinente. `docs/probe-torch-cpu.json`. Não é avaliação independente nem medição de latência da GPU em nuvem.
- Transporte completo da ponte Gradio/HTTP testado com um test double explicitamente identificado; servidor temporário de desenvolvimento encerrado. `docs/teste-ponte-gradio.json`.
- Ambiente original: 52 testes passaram, um módulo PyTorch foi pulado por não ser dependência desse ambiente. Ambiente de nuvem: 53 testes passaram, excluindo explicitamente o arquivo de testes do treino MLX, indisponível nesse backend. Testes adicionais do publicador protegem revisão remota e conteúdo do pacote; totais finais no registro de validação.
- Nenhuma dependência da `.venv` original ou de outros projetos foi atualizada. O ambiente novo é `deploy/hf-space/.venv`, com Python 3.12 e prompt `venv-citizentech-cloud`.

## Validação de execução hospedada

A primeira chamada pública FP16 retornou502 por geração inválida e foi preservada em `docs/teste-api-publica.json`. A configuração ativa usa FP32 com `matmul` de precisão mais alta; duas chamadas conhecidas responderam200 em aproximadamente4,67s e2,35s de tempo total observado. A primeira registrou a observação sem inventar causa; a segunda reconheceu que o custo não constava. `docs/teste-api-publica-fp32.json`. Leitura de conteúdo pelo mesmo agente de IA, não revisão humana independente, novo benchmark ou reestimativa de alucinação. Não houve reparação de JSON ou tentativa oculta até acertar dentro de uma chamada.

O serviço público oferece uma demonstração interativa e endpoints HTTP para consumo por aplicações. A hospedagem gratuita inclui cotas e filas, portanto a disponibilidade pode variar durante a correção.

O placar v5 permanece histórico e não foi reescrito. A migração preserva a especialização, mas CPU/GPU e frameworks podem produzir diferenças numéricas e respostas distintas. Não apresentar a paridade de módulos ou uma chamada bem-sucedida como validação universal do conteúdo.

[Instruções de implantação](../../deploy/hf-space/README.md). Backup anterior de README, instruções do projeto e nota do Obsidian em `docs/backup.json`. Restauração documental por comparação/cópia ao caminho original, preservando alterações posteriores. Nenhuma regra global foi alterada.
