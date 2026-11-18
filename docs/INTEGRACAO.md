# Integração do componente de IA — estado atual

Revisado em12/11/2026 contra o PDF fornecido pelo usuário (páginas18–24,29 e48). O usuário confirmou que não há orientação adicional do professor e que as partes dos colegas ainda não estão disponíveis.

## Produto integrado e entregas separadas

A página24 prevê um envio no Teams de cada disciplina, realizado por um integrante em nome da equipe. Isso organiza a submissão; não elimina a exigência de um produto comum. A página18 exige um único produto por equipe atravessando as sete disciplinas; a21 pede componentes comunicando por contratos claros; a29 pede a LLM integrada ao produto. A página48, item06 de RPA, exige que o resultado da automação seja consumido por outro componente.

É possível dividir o desenvolvimento e os responsáveis por disciplina. O PDF não determina que tudo esteja no mesmo processo nem que cada componente se comunique diretamente com todos os demais. O fluxo mostrado pelo MVP precisa ser coerente e funcionar naquilo que se propõe a demonstrar. O mínimo exato de integração aceito na avaliação não é especificado como uma lista de chamadas entre todas as disciplinas; deve ser alinhado na arquitetura e, se necessário, com os professores. Não apresentar um consumidor de referência ou uma página isolada da IA como prova de conexão dos componentes reais do grupo.

## Serviço atual: Qwen2.5-1.5B treinado

Na raiz `/Users/lucasmanentti/Projects/citizentech-iluminacao-ia`, com o ambiente existente:

```zsh
.venv/bin/python scripts/servir_1_5b.py
```

Demonstração em `http://127.0.0.1:8000/demo`; documentação interativa em `http://127.0.0.1:8000/docs`. Encerrar com Control+C. O comando `citizentech serve` também usa1.5B; a versão histórica exige `--legacy-v2`. O adaptador r1 foi selecionado pela validação e a POC executa a LLM real. Sem artefatos válidos, /ready e /v1/analisar retornam503, sem fallback. Não instala dependências, baixa pesos ou inicia treino.

O contrato de `docs/openapi.json` foi comparado ao OpenAPI gerado pelo código atual e coincide. Chamada POST `/v1/analisar`, JSON com `ocorrencia_id`, `pergunta`, `simulada` e pelo menos uma observação em `relato`, `sensores` ou `observacoes_visuais`. Datas exigem offset explícito. `simulada` deve refletir a origem dos dados. Declaração de calibração exige referência, mas não certifica a leitura. ADC bruto não pode ser convertido implicitamente em lux.

Exemplo simulado para validar o contrato, sem constituir integração do grupo:

```json
{"ocorrencia_id":"SIM-001","pergunta":"O que pode ser registrado sem determinar uma causa?","simulada":true,"relato":"Luminária pública observada apagada durante a noite. A causa não foi inspecionada.","sensores":[],"observacoes_visuais":[]}
```

Cliente de referência, em outro terminal na raiz:

```zsh
.venv/bin/python examples/cliente.py --arquivo examples/ocorrencia.json
```

## Resposta e falhas

- HTTP200: envelope com `request_id`, identificação da ocorrência, análise, referências e versão da execução. Pode conter análise ou recusa válida. Transporte/esquema corretos não garantem conteúdo correto.
- HTTP413: corpo acima de32KiB;422: entrada ou contexto inválido;429: inferência em andamento (respeitar Retry-After);502: saída inválida da LLM;503: indisponibilidade/falha do backend.
- O consumidor deve exibir fontes, limites e informações faltantes, e preservar o encaminhamento humano. Não deve transformar a resposta em diagnóstico elétrico ou acionar reparo automaticamente.
- Correlacionar por request_id sem registrar relatos/dados pessoais em logs públicos. Tratar timeout e indisponibilidade explicitamente, sem substituir por uma conclusão inventada.

## Plano de conexão — depende das partes do grupo

1. Equipe define componentes, responsáveis, estruturas de dados e um fluxo único do produto. Esta revisão não escolhe infraestrutura ou fornecedores pelos colegas.
2. Quando existirem, inspecionar os repositórios e adaptar o consumidor ao contrato. Entradas de sensor/visão devem manter unidade, origem, calibração declarada e limitação; não supor que a LLM processa diretamente fotografia ou controla robô.
3. Consumidor real envia a ocorrência, recebe a análise e apresenta o resultado no fluxo do produto, com intervenção humana quando pertinente.
4. Validar ponta a ponta: observação respondível, dado ausente, conflito, indução no relato, saída inválida e serviço indisponível. Registrar versões, request_id e evidências sem dados sensíveis.
5. Consolidar a Ficha Técnica comum nos documentos das disciplinas, relacionando onde cada componente entra no MVP. A entrega em cada Teams segue seu formato próprio.

**Estado atual:** treinamento1.5B,seleção,comparaçãoA/B/C e POC locais concluídos. Seis chamadas reais retornaram200; houve uma respostaADC parcial/incerta e citaçãoCPFL indevida no caso de técnico,registradas separadamente. Partes dos colegas não disponibilizadas; consumo pelo produto real do grupo continua pendente. Ver o relatório atual para qualidade/limitações.

## Publicação e disponibilidade

O serviço inicia somente em127.0.0.1. MLX requer Apple Silicon; um container Linux/CUDA não executa este backend MLX automaticamente. A publicação precisa de arquitetura e ambiente compatíveis, política de acesso, custos e responsabilidade definidos pelo grupo; não se presume Mac pessoal exposto, túnel ou hospedagem gratuita. Preparar configuração não equivale a deploy comprovado. O PDF exige MVP e links acessíveis na correção; o serviço local não cumpre sozinho essa etapa.
