# Verificação limitada de citações —17/11/2026

## O que foi ativado

A POC mantém o modeloQwen2.5-1.5B/r1,os pesos,o prompt,a busca e o corpus originais de v5. Foi acrescentada **uma guarda de compatibilidade documental** na saída daAPI: os trechos genéricos `cpfl-reparos:1` e `sp-faq:1` não contêm designação de profissional/equipe,identificadores de ordem/protocolo,contrato/garantia específicos ou preço de reparo. Quando a pergunta explicitamente pede esses dados e a resposta usa esses trechos como citação, aAPI rejeita a análise e devolve502,com código `fonte_incompativel` e aviso para conferir o documento operacional com uma pessoa.

Não troca fontes,não preencheJSON,não altera status,não refaz inferência e não usa resposta gravada. O modelo continua podendo errar. Esse é um bloqueio de incompatibilidades conhecidas,baseado em termos da pergunta e no alcance verificado desses dois documentos; **não é um verificador geral de implicação semântica nem prova de veracidade**. Pode deixar passar outros erros e pode rejeitar consultas ambíguas. Fontes/documentos novos precisam de revisão explícita da política. Uma rejeição é falha sinalizada,não resposta correta para a tarefa nem redução medida de alucinação do modelo.

O frontAkona foi preservado e já exibe o erro daAPI sem apresentar o resultado como análise validada. Limites32KiB e contratos originais preservados. Erros têm request_id e log de código/status,sem registrar o relato no novo log. O envelope de erro continua o contrato existente; não se adicionou campo à análise.

## Como abrir

Na raiz do projeto:

```zsh
.venv/bin/python scripts/servir_poc_validada.py
```

Abrir `http://127.0.0.1:8000/demo`,encerrar comControl+C no terminal. O serviço é apenas local e usa o adaptador já selecionado. Não precisa instalar,baixar ou treinar. O comando antigo `scripts/servir_1_5b.py` e aCLI `citizentech serve` permanecem como reprodução daAPI original,**sem esta guarda adicional**. Não iniciar as duas versões na mesma porta.

## Verificação realizada

44 testes de software passaram,com testes escritos antes da implementação da guarda e análise estática aprovada. Testes cobrem fonte incompatível recusada sem reescrever análise,fonte pertinente preservada,uma única inferência,erro comrequest_id,limites de entrada eJSON inválido. Geradores falsos são identificados nos testes e não equivalem a validação factual.

NaAPI com modelo real,quatro regressões conhecidas:caso de técnico com citaçãoCPFL foi bloqueado com502;perguntas de custo ausente,registro noturno e conflito responderam200 com o adaptador original. Não é teste independente nem taxa de qualidade. Registros completos em `docs/api-real.json`;congelamentos/código/fontes v5 preservados conferidos em `docs/validacao.json`. Página servida e prontidão verificadas;inspeção visual no navegador não executada por indisponibilidade do acesso local previamente registrada.

O placar,notebook,90 respostas e evidência de alucinação de v5 **não foram alterados,reavaliados ou substituídos**. O usuário decidiu manter essa evidência. Houve inferência de comparação experimental,mas **nenhum novo treinamento** ou mudança dos pesos.

## Tentativas que não foram ativadas

- `experimentos/v6-fundamentacao`:novo procedimento de equipe,instruções ampliadas e termos de busca. Em12 casos adicionais houveJSON incompleto e uma frase de desenvolvimento sobre não poder solicitar documento sem suporte. Rejeitada;saídas e congelamento preservados. Ajustes posteriores em imports foram só formatação,com código de execução original arquivado.
- `experimentos/v6b-busca`:alteração somente do procedimento/aliases de lacuna,com prompt original. Melhorou a fonte em consultas de equipe,mas um novo caso de custo perdeu as seis chavesJSON;11/12 conformes contra12/12 daoriginal. Não passou a regra predefinida e não foi ativada. Os dois conjuntos adicionais têm autoria porIA relacionada,não independência humana/campo.

Não apresentar esses resultados como prova geral de melhoria. `scripts/servir_poc.py`,que apontava à primeira candidata,rejeita inicialização para evitar uso acidental. A única versão nova ativa é a guarda limitada sobre a geração v5 original. O erro de recusar custo como fora do escopo e outros defeitos do modelo **não foram resolvidos de forma geral**;permanecem documentados. Corrigir a geração de forma robusta exigiria outro ciclo,com treino/dados separados e avaliação nova,se solicitado. Não apagar as tentativas malsucedidas ou retreinar sobre seus testes para alegar acerto não visto.

## Preservação e restauração

Backup antes da tarefa:`/Users/lucasmanentti/.codex/backups/citizentech-fundamentacao-20261117-224103`,com manifesto da página/guia/notas. As demais mudanças de inferência foram criadas em arquivos novos;nenhum arquivo preditivo congelado de v5 foi modificado. Para voltar ao comportamento original,encerrar o serviço atual e iniciar `.venv/bin/python scripts/servir_1_5b.py`. Para restaurar documentação,comparar/copiar do manifesto ao caminho original,preservando alterações posteriores. Não remover dados,ambientes ou pesos. Sem instalação,commit,push,deploy,exposição externa ou nova regra global.
