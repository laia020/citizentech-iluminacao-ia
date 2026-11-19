# Implantação independente do Mac

Esta pasta contém o ambiente e o inicializador da versão Hugging Face Spaces/ZeroGPU. A aplicação mantém a tela Akona e o contrato de dados e HTTP `/v1/analisar`. A ponte para a fila GPU usa loopback dentro da própria instância de nuvem; não há ngrok, Cloudflare Tunnel ou dependência de serviço no Mac pessoal.

## Preparar o ambiente de desenvolvimento

Python 3.12, conforme este `pyproject.toml` e `.python-version`. Em cópia nova, somente quando o ambiente abaixo ainda não existir:

```zsh
uv venv --python 3.12 --prompt "venv-citizentech-cloud" deploy/hf-space/.venv
uv sync --project deploy/hf-space --locked
```

Preservar a `.venv` original do projeto. O ambiente separado usa PyTorch 2.13.0, Gradio 6.32.0 e a versão de `spaces` exigida pela plataforma: 0.51.3 na implantação de 18/11/2026; 0.52.1 na atualização de 19/11/2026. Não instalar MLX no servidor Linux ou substituir dependências de outros projetos. O arquivo `requirements.txt` é exportado do lockfile próprio deste ambiente.

Na publicação da página de RPA em 19/11/2026, o build passou a injetar `spaces==0.52.1`, conflitante com o pin anterior; a primeira tentativa falhou antes da inicialização. O lockfile foi atualizado somente para essa nova versão. `requests==2.34.2`, também injetado pela plataforma, passou a ser dependência direta para preservar a versão já fixada e seus transitivos. A comparação dos dois lockfiles confirmou que nenhuma outra versão de pacote mudou. O wheel oficial de `spaces` 0.52.1 mantém o alias `spaces.zero.startup` usado pelo inicializador. Não houve alteração dos pesos, prompt, dados ou contrato de análise. A disponibilidade efetiva é registrada na validação da publicação, não presumida pela atualização das dependências.

```zsh
uv export --project deploy/hf-space --locked --no-dev --no-hashes --no-emit-project --format requirements-txt --output-file deploy/hf-space/requirements.txt --quiet
```

## Pacote e publicação

Autenticar a conta no fluxo de navegador do `hf auth login`; não guardar tokens no código ou no Space público. A preparação abaixo é local e não publica:

```zsh
.venv/bin/python scripts/preparar_space.py --destino experimentos/v7-nuvem/runs/space-bundle-NOVO
```

O preparador valida o adaptador selecionado e o congelamento, copia somente arquivos necessários e gera SHA-256 de todos os arquivos. O ZIP original do adaptador acompanha o pacote; a base oficial é obtida pela hospedagem na revisão fixada. Nomes existentes são recusados.

`scripts/publicar_space.py --help` documenta a publicação explícita. O publicador confere integridade, arquivos extras, dono autenticado e hardware gratuito `zero-a10g`. Não troca para hardware pago se a elegibilidade gratuita falhar. Space existente exige revisão remota inspecionada em `--atualizar-revisao`; mudanças concorrentes são recusadas, com `parent_commit` no envio. Não apaga arquivos remotos por padrão.

O inicializador `app.py` exige ambiente Spaces e não inicia hospedagem no Mac. A base é carregada em FP32 e CUDA emulado no início do Space; inferência ocorre somente na função com `spaces.GPU`. Como a aplicação usa `mount_gradio_app` em vez de `Blocks.launch`, chama explicitamente o hook de inicialização `spaces.zero.startup` da versão fixada, após registrar a função GPU. Isso realiza o mesmo relatório/empacotamento esperado pela biblioteca; não desativa checagens ou altera limites do provedor. A rota HTTP e a fila exigem marcação de dados fictícios e compartilham validações de JSON, referências e guarda de citações.

## Validar antes de declarar pronto

1. Confirmar hardware `zero-a10g`, build concluído e `/ready` disponível.
2. Fazer chamadas públicas com observação respondível, dado ausente e fonte incompatível; examinar conteúdo, não apenas HTTP.
3. Conferir identificação da base, revisão e SHA do adaptador na resposta.
4. Confirmar que nenhum processo local atende o serviço; iniciar/encerrar testes de desenvolvimento não é hospedar o produto no Mac.
5. Registrar quotas/filas e falhas explicitamente. Modelo carregado não garante cota GPU disponível.

Reproduções e estado da implantação: [ciclo de migração](../../experimentos/v7-nuvem/README.md). O serviço também pode ser consumido por sistemas externos usando o contrato JSON descrito em `docs/INTEGRACAO.md`.

## Evidências e limites

Os 32 módulos LoRA originais foram comparados com `mlx_lm.tuner.lora.LoRALinear`, em entradas fixas F16 e pesos-base zerados, sem fusão: todos passaram na tolerância registrada. Esse teste não comprova equivalência do Transformer inteiro entre CPU e CUDA. Um exemplo conhecido da POC também foi executado no Qwen1.5B real em PyTorch CPU, usando a base oficial já existente e o adaptador original, sem baixar pesos ou treinar novamente.

Não transferir automaticamente o placar científico MLX para este backend. A primeira chamada pública em FP16 foi rejeitada por saída inválida; o registro foi mantido. A implantação ativa FP32 respondeu adequadamente aos dois casos conhecidos testados, sem repetir gerações dentro de uma requisição, reparar JSON, retreinar ou mudar prompt/busca. Isso não demonstra qualidade geral ou ausência de alucinação. A hospedagem gratuita tem cotas/filas e não garante disponibilidade contínua. Nenhum plano pago foi contratado.
