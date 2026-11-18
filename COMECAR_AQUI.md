# Abrir a POC1.5B treinada

## Acesso público atual — 18/11/2026

**[Abrir a IA na nuvem](https://laia020-citizentech-iluminacao-ia.hf.space/demo).** Modelo, API e tela executam no Hugging Face; o Mac pode permanecer desligado. Selecione um exemplo fictício ou escreva uma observação simulada. A hospedagem gratuita tem cotas/filas e pode ficar indisponível temporariamente. Dois exemplos conhecidos foram testados pela API pública, com resposta pertinente; isso não garante ausência de erros.

[API pública](https://laia020-citizentech-iluminacao-ia.hf.space/docs), [validação da implantação](experimentos/v7-nuvem/docs/VALIDACAO-NUVEM.json). A ligação com o Akona dos colegas continua pendente do repositório deles.

## Reprodução local opcional — não é a hospedagem da entrega

O fine-tuning e a avaliação local terminaram. A versão atual usa **Qwen2.5-1.5B-Instruct + RAG + LoRA**, com adaptadorr1 selecionado.

Se o serviço já estiver ativo, abra <http://127.0.0.1:8000/demo>. Para iniciá-lo após fechar o serviço ou acordar o Mac:

```zsh
cd /Users/lucasmanentti/Projects/citizentech-iluminacao-ia
.venv/bin/python scripts/servir_poc_validada.py
```

Mantenha esse terminal aberto. Escolha um cenário fictício ou **Meu próprio cenário fictício**, escreva pergunta e observações e clique para analisar. A resposta é gerada pelo modelo local; fontes e resposta completa ficam disponíveis para conferência. Para encerrar, Control+C no terminal em que iniciou. O primeiro carregamento leva alguns segundos.

Não é necessário instalar, baixar pesos ou treinar novamente. A interface e a API são locais; o professor poderá usá-las neste Mac acordado. Acesso externo/URL pública ainda depende de implantação autorizada.

O modelo ainda erra. Os cinco exemplos e uma pergunta livre tiveramHTTP200, mas há uma resposta composta sobre ADC com adequação incerta e uma citaçãoCPFL não pertinente na pergunta de técnico. Não confundir resposta válida com diagnóstico ou verificação de campo. [Roteiro da POC](POC_PARA_PROFESSOR.md) e [relatório completo](experimentos/v5-1.5b/docs/RELATORIO-1_5B.md).

CLI histórica7B exige `--legacy-v2`. A versão500M foi removida por autorização; não está ativa nem disponível para fallback.

## Verificação adicional de fontes

A POC atual bloqueia incompatibilidades documentais conhecidas. Uma pergunta sobre técnico designado que cite a página genéricaCPFL,por exemplo,recebe erro explícito em vez de ser apresentada como validada. Isso não corrige automaticamente a resposta nem garante todas as fontes. [Escopo,testes e limitações](experimentos/v6c-validacao/README.md). O comando anterior e `citizentech serve` reproduzem aAPI original sem a guarda;usar o comando acima para a versão atual.
