# Página de RPA no site Akona Energy

A rota `GET /rpa` apresenta a execução histórica do RPA com dados fictícios, no mesmo site da demonstração de IA. O menu de `/demo` permite abrir a página e há navegação de retorno. Esta alteração não executa lotes, inicia inferência, altera pesos ou modifica o contrato de `POST /v1/analisar`.

## Origem do conteúdo

- Repositório: <https://github.com/laia020/citizentech-rpa>.
- Revisão das evidências: `68c69091d9b74afc365573fc3577428f077900de`.
- Execução: <https://github.com/laia020/citizentech-rpa/actions/runs/44327757282>.
- Execução RPA: `dd5f0bb6ea1f4cd6bd39db4fa78b0385`, em 18/11/2026, às 11:45 de Brasília.
- Fontes preservadas: `resumo.json`, `resultados.json`, `pendencias.json`, `auditoria.jsonl` e `github-run.json`, na pasta `docs/evidencias/nuvem-real/` do RPA.

São quatro entradas: duas processadas, uma duplicada e uma pendente, sem falhas de execução. Houve duas chamadas à API de IA, ambas HTTP 200. A duplicata reaproveitou a primeira resposta e o registro sem observação não foi enviado à IA. Informação insuficiente é um resultado da análise, não uma falha de transporte. A linha pendente não possui identificador de ocorrência ou request ID no resultado exportado; a página não atribui identificadores a ela.

Os links das evidências e do PDF estão fixados na revisão acima, sem depender dos artefatos temporários do Actions. Os arquivos existentes no repositório de RPA foram preservados. Não há comprovação de abertura de chamados no backend do Akona, diagnóstico elétrico ou impacto municipal.

## Sequência sugerida para o vídeo de até três minutos

1. **0:00–0:25:** abrir `/rpa` e explicar o objetivo de validar e organizar um lote de relatos.
2. **0:25–0:55:** apresentar o fluxo de entrada, validação/deduplicação, IA, auditoria e revisão humana.
3. **0:55–1:50:** mostrar as contagens e os quatro tratamentos. Abrir os detalhes da duplicata e da pendência; explicar por que apenas duas entradas consultaram a IA.
4. **1:50–2:35:** abrir a execução no Actions e os resultados ou a auditoria. Mostrar a correlação pelo request ID e abrir a seção de falha histórica HTTP 503 para demonstrar as tentativas limitadas e o registro do erro.
5. **2:35–2:55:** indicar o relatório e o código, esclarecer os dados fictícios e a necessidade de revisão humana.

Os tempos são um planejamento, não duração medida. O vídeo ainda precisa ser gravado e publicado. Esta página apresenta evidências existentes; não deve ser narrada como execução iniciada ao vivo. A pendência de entrada não substitui a demonstração de falha técnica: a seção de falha HTTP 503 aponta para o resumo e a auditoria originais de `real-indisponibilidade/`, na mesma revisão fixa, e distingue suas contagens das do lote bem-sucedido.

## Implementação e verificação

A página é HTML estático, sem JavaScript, formulário, polling ou dependências novas em produção. Um único roteador lê `src/citizentech_ia/v5/rpa.html` em UTF-8 e é incluído na aplicação em nuvem e na aplicação de desenvolvimento, evitando que o menu compartilhado aponte para uma rota inexistente. O acesso independe da prontidão/fila de inferência. O preparador existente copia toda a pasta `src`, incluindo a página e suas fontes incorporadas, e registra seu hash no manifesto do pacote. Preparador e publicador usam caminhos POSIX no manifesto, permitindo verificar no Windows o pacote destinado ao Linux; a tela de IA também é lida e gravada explicitamente em UTF-8.

Testes principais em `tests/test_pagina_rpa.py`: acesso com modelo indisponível e fila ocupada, preservação das contagens/identificadores, navegação, referências de acessibilidade e empacotamento. A suíte usa componentes simulados e não baixa pesos-base nem executa inferência.

Nesta cópia Windows foi criado ambiente `.venv` separado com Python 3.12 e dependências fixadas pelo lockfile raiz, sem o extra de treinamento MLX. Para verificar o pacote e os testes existentes da nuvem, foram acrescentados somente nesse ambiente `safetensors==0.8.0` e `huggingface-hub==2.4.0`, conforme as versões de implantação. Nenhum lockfile ou ambiente global foi alterado. Executar os testes em modo UTF-8 no Windows:

```powershell
.venv/Scripts/python.exe -X utf8 -m pytest tests/test_pagina_rpa.py tests/test_nuvem.py tests/test_publicacao_space.py tests/test_principais.py -q
```

Verificação desta implementação em 19/11/2026: **60 testes aprovados, um módulo de testes pulado por ausência de PyTorch**, executando `python -X utf8 -m pytest --ignore=tests/test_treino_estavel.py -q`. O módulo de treinamento MLX foi excluído por exigir macOS; não foi alterado para este trabalho. Os dez links externos da página responderam HTTP 200. O pacote real foi preparado com 89 arquivos, adaptador original e hashes conferidos. Nenhuma nova chamada à IA pública foi realizada. Registro completo e localização do ZIP: [VALIDACAO-PAGINA-RPA.json](VALIDACAO-PAGINA-RPA.json).

A revisão visual em computador e celular não foi concluída: a ferramenta de controle do Brave interrompeu a interação por não conseguir confirmar a URL com segurança. Há estilos responsivos, navegação por teclado com HTML nativo e verificações automatizadas de referências/ARIA, mas isso não equivale a validação visual ou auditoria completa de acessibilidade. O servidor temporário de prévia, limitado a `127.0.0.1` e sem inferência, foi encerrado.

## Publicação e restauração

A implementação local não torna `/rpa` automaticamente pública. É necessário preparar um novo pacote com `scripts/preparar_space.py` e seguir o publicador existente, conferindo a revisão atual do Space e preservando o hardware gratuito `zero-a10g`. Não publicar com uma revisão remota desatualizada nem substituir a hospedagem por um serviço na máquina pessoal. Em 19/11/2026, o usuário solicitou continuar após o pedido de autorização para commit, push e atualização do site. Essa autorização cobre a publicação desta página, sem gastos ou mudanças no modelo; o resultado efetivo da implantação será registrado separadamente.

Antes das alterações, foram salvos backups datados de `README.md`, da tela original, do proxy, do preparador e da configuração Git local, em uma pasta temporária `citizentech-ia-rpa-20261119-*`. Para restaurar, copiar apenas os arquivos desejados do backup sobre os correspondentes desta cópia; preservar eventuais alterações posteriores. O Git também mantém a versão original na revisão `40d76bbfa33e089cf1e8a3a90f9ba34e2011c397`. Após uma publicação, a reversão deve reutilizar o pacote anterior verificado e conferir novamente a revisão remota.
