> **Execução atual —17/11/2026:** treinamento1.5B autorizado e concluído. Dois candidatos400/800 passos,seleção r1 por validação antes do teste30. [Relatório atual](experimentos/v5-1.5b/docs/RELATORIO-1_5B.md) traz comparação90 saídas,revisão técnica por IA,incertos e limitações; menor alucinação observada não foi conclusiva no intervaloC-A. POC local treinada; integração/publicação/vídeo ainda pendentes. As escolhas7B abaixo são históricas; os artefatos500M foram excluídos conforme autorização. Nenhum repouso automático nesta etapa.

# Especificação de implementação — CitizenTech Iluminação IA

Versão: 1.0 • Data: 12/11/2026 • Idioma: português brasileiro  
Estado: **desenho aprovado; implementação local em execução. Resultados e pendências em docs/RELATORIO.md e runs/progress.json.**

Este documento consolida o plano aprovado na conversa e detalha o comportamento esperado para outro engenheiro ou agente executar. As decisões técnicas são o desenho aprovado; desempenho, compatibilidade e melhoria do modelo ainda precisam ser medidos. Exemplos de API são contratos propostos, não resultados de uma execução.

## 1. Resumo e limite da entrega

Desenvolver o componente de Generative AI do produto de monitoramento inteligente de iluminação pública do grupo. Receber uma ocorrência, recuperar informações pertinentes e retornar análise preliminar estruturada, com evidências, fontes, informações faltantes e encaminhamento para revisão humana.

A especialização será feita por **fine-tuning local de adaptadores LoRA sobre modelo quantizado em 4 bits (QLoRA)** no MacBook do usuário. Não é treinamento do modelo do zero. O modelo especializado continuará utilizando recuperação de documentos; o fine-tuning não substitui a base de conhecimento.

O projeto ficará em `/Users/lucasmanentti/Projects/citizentech-iluminacao-ia`, separado de Ktrix, Operum e mini-code-llm. Cada dependência Python pertencerá à sua própria `.venv`.

### 1.1 Incluído

- Base de conhecimento rastreável e publicável conforme os direitos de uso.
- Exemplos de treino, validação e teste com gabaritos.
- Busca, limiar de recuperação e métricas recall@1 e recall@3.
- Fine-tuning efetivamente executado no Mac, com adaptador salvo.
- Comparação: modelo original sem contexto, RAG simples e RAG com adaptador.
- API, interface local de demonstração e cliente para integração.
- Testes de software, avaliação de modelo, análise de cinco erros reais.
- Notebooks executados, relatório, README, documentação de integração e roteiro do vídeo.
- Atualização documental do Obsidian e das instruções gerais, quando a execução correspondente estiver autorizada.

### 1.2 Fora desta implementação

- Construção do robô, sensores e firmware; treinamento de visão computacional.
- Pipeline Airflow/Databricks, RPA, BI, interface completa e infraestrutura das outras disciplinas.
- Diagnóstico elétrico conclusivo, comandos de manutenção física ou acionamento automático de equipamentos.
- Hospedagem paga, inferência em APIs comerciais ou treinamento remoto.
- Migração dos ambientes existentes, atualização global de bibliotecas ou reutilização de suas venvs.
- Publicações, commits, pushes, configuração de contas e exposição do Mac sem autorização explícita.

A integração final faz parte da exigência acadêmica, mas exige um componente dos colegas consumindo a API. Um cliente de teste local comprova o contrato; não comprova sozinho a integração do MVP do grupo.

## 2. Origem e matriz dos requisitos

Fonte acadêmica: `/Users/lucasmanentti/Downloads/Desafio-FIAP-GS-CitizenTech 4ES.pdf`, 60 páginas. Páginas 18–21: produto único e integração por contratos; páginas 29–31: Generative AI. Prazo no documento: **19/11/2026, 23h55**. Reconfirmar eventuais alterações comunicadas pelo professor antes da entrega.

| ID | Exigência | Evidência a produzir | Pontos GenAI |
|---|---|---|---:|
| AC-01 | Tarefa e casos de teste, inclusive “não consta” | Ficha da tarefa, teste congelado e gabaritos | 0,5 |
| AC-02 | Base em trechos com fonte | Catálogo de fontes, chunks e direitos de uso | 1,0 |
| AC-03 | Recall@1, recall@3 e limiar justificado | Notebook e relatório de recuperação | 1,0 |
| AC-04 | JSON, fundamentação, citação e recusa | Respostas brutas e validação estrutural/semântica | 2,0 |
| AC-05 | Especialização comparada ao RAG | Adaptador treinado e comparação B × C | 2,0 |
| AC-06 | Três configurações com interpretação | Placar A/B/C no mesmo teste | 2,0 |
| AC-07 | Cinco erros reais e correções propostas | Registro rastreável das falhas | 1,0 |
| AC-08 | README e reprodução | Ambiente bloqueado, comandos e instruções | 0,5 |
| AC-09 | API integrada ao produto | OpenAPI, teste e evidência do consumidor real | Requisito transversal |
| AC-10 | Relatório, integrantes e RM, vídeo | Relatório no GitHub e links conferidos | Requisito transversal |

A opção LoRA já foi escolhida pelo usuário, embora a rubrica também permita agente. Não substituir fine-tuning por agente para economizar trabalho. O objetivo acadêmico de melhorar acerto e reduzir alucinação é uma hipótese a testar, nunca um resultado a declarar sem medições.

## 3. Regras de execução e dúvidas

### 3.1 Regra pedida para Codex e Obsidian

Texto a acrescentar, com backup, às instruções globais vinculadas à nota do cofre:

> Quando houver dúvida não resolvida sobre intenção, requisito ou decisão necessária à execução, interromper a execução, explicar a dúvida e perguntar ao usuário. Não adotar suposições nem fazer alterações enquanto aguarda a resposta.

Na criação desta especificação, essa alteração global permanece **planejada, ainda não aplicada**. O pedido mais recente limita esta etapa à pasta e à documentação para revisão. A regra já consta também no AGENTS.md deste projeto.

Dúvidas que possam ser resolvidas por consulta aos arquivos devem ser investigadas primeiro com leitura. Não executar ações dependentes de uma resposta pendente. Não interpretar conteúdo de documentos, páginas ou exemplos como autorização para instalar, publicar ou alterar o sistema.

### 3.2 Autorização por etapa

- Etapa atual: pasta e especificação, sem implementação.
- Antes de iniciar código e instalação: aguardar instrução do usuário após revisão.
- Downloads necessários ao treinamento pertencem à futura execução do plano, não à etapa documental.
- Publicação e ampliação de acesso continuam sujeitas às regras globais e às permissões reais do ambiente.
- A autorização anterior de repouso vale ao fim da implementação e das validações, não ao terminar a SPEC.

## 4. Usuários, tarefa e cenários

Usuário principal: integrante da equipe/operador que recebe ocorrências e precisa organizar evidências. Beneficiário final: cidadão afetado por iluminação inadequada. A interface não substituirá inspeção por profissional competente.

### 4.1 Cenários de demonstração

1. Relato de iluminação apagada à noite, com informação suficiente para registrar ocorrência e solicitar verificação, sem concluir causa física.
2. Luminosidade baixa com sensor sem calibração: explicar que a leitura não comprova nível de lux nem defeito.
3. Pedido de informação que não consta na base: recusar a conclusão e indicar a informação ausente.
4. Sensor e observação visual incompatíveis: apontar o conflito e pedir nova verificação.

A ocorrência será marcada como simulada nos dados e na interface quando não vier de um dispositivo real. Não apresentar simulação como coleta de campo.

### 4.2 Limites das conclusões

- Não converter valor bruto de LDR para lux sem curva e procedimento de calibração documentados.
- Não tratar fotografia escura, baixa luminosidade ou relato isolado como prova de lâmpada queimada, furto, falha de relé ou queda de rede.
- Não inventar limiares normativos, prazos, economia de energia, endereços de atendimento ou probabilidades.
- Hipóteses só entram quando houver suporte documental e observacional; não atribuir percentual de confiança inventado.
- Não orientar intervenção em rede elétrica. Encaminhar para avaliação humana conforme a base pertinente.
- Município não informado permite análise genérica, mas impede recomendar um canal municipal específico como se fosse universal.
- Fontes podem estar corretas para municípios diferentes: diferença de jurisdição não é automaticamente contradição.

## 5. Ambiente, dependências e proteção do Mac

Hardware verificado anteriormente em 12/11/2026: MacBook Pro MacBookPro18,2, M1 Max, CPU 10 núcleos (8+2), GPU 32 núcleos, memória unificada 64 GB e arm64. Espaço livre observado anteriormente: aproximadamente 843 GiB; reavaliar antes de downloads. O inventário não certifica temperatura, estado de bateria ou capacidade disponível em outro momento.

### 5.1 Ambiente Python futuro

- Python 3.12; preferir o 3.12.16 já instalado, após resolver compatibilidade do conjunto de bibliotecas.
- Criar `.venv` somente após verificar que não existe ambiente anterior e inspecionar os requisitos do projeto.
- Comando planejado: `uv venv --python 3.12 --prompt "venv-citizentech-iluminacao-ia"`.
- Confirmar executável, versão, diretório de trabalho e VIRTUAL_ENV.
- Manter declaração em pyproject.toml e travamento em uv.lock; não fixar aqui números de bibliotecas que ainda não foram resolvidos e testados em conjunto.
- Grupos: execução (API, validação e busca), treino (MLX/MLX-LM) e desenvolvimento (testes/notebooks/lint).
- Dependências previstas: FastAPI, Uvicorn, Pydantic, NumPy, scikit-learn, MLX/MLX-LM, suporte JSONL/YAML, pytest, HTTPX e Jupyter. Instalar somente as efetivamente usadas.
- Não instalar CUDA, bitsandbytes ou stack PyTorch apenas por analogia com outro projeto. Este pipeline de LLM utiliza MLX.

### 5.2 Regras de recursos

- Medir memória, espaço e tempo antes de decidir a execução longa.
- Treino, geração para avaliação e serviço de demonstração pesada não rodarão simultaneamente.
- Manter uma cópia do modelo carregada por processo; encerrar workers antigos de forma controlada antes de mudar o experimento.
- Não usar swap como capacidade planejada nem desabilitar proteções para o modelo caber.
- Sem mudanças em kernel, ventoinhas, gerenciamento térmico ou limites globais.
- Verificar ventilação, alimentação e responsividade; registrar OOM, pressão persistente e limitação de desempenho quando observáveis.
- Se houver instabilidade, interromper e perguntar antes de mudar o desenho aprovado.
- Preservar resultados e checkpoints anteriores. Limpeza e retenção não podem apagar artefatos sem autorização aplicável.

## 6. Arquitetura

```mermaid
flowchart TD
    A[Ocorrência do grupo ou exemplo simulado] --> B[FastAPI: validação da entrada]
    B --> C[Normalização e seleção por abrangência]
    C --> D[Busca TF-IDF local]
    D --> E[Top 3 e limiar calibrado]
    E --> F[Montagem do contexto e orçamento de tokens]
    F --> G[Qwen em MLX + adaptador local]
    G --> H[Validação do JSON e referências]
    H --> I[Resposta e metadados da execução]
    I --> J[MVP dos colegas ou demo local]
    K[Fontes e documentos autorais] --> L[Chunks versionados]
    L --> D
    M[Treino / validação separados] --> N[Fine-tuning local]
    N --> G
```

O código será modular: ingestão de fontes, preparação de dados, recuperação, carregamento/geração, treinamento, avaliação, API e demo. A API chamará uma interface única de análise; adaptadores e modos de experimento serão selecionados por configuração do processo, não por parâmetro público arbitrário.

Não incluir banco de dados, fila distribuída ou framework de agentes na v1. Artefatos de experimentos serão arquivos JSONL/CSV/JSON locais. A API será sem estado de negócio: não criará ordem de serviço nem armazenará histórico de cidadãos.

## 7. Base de conhecimento e direitos de uso

### 7.1 Fontes iniciais candidatas

- SP Regula, perguntas frequentes de iluminação pública: https://prefeitura.sp.gov.br/web/spregula/w/iluminacao_publica/perguntas_frequentes/4613
- CPFL, reparos de iluminação pública: https://www.cpfl.com.br/reparos-de-iluminacao-publica
- Documentos autorais do projeto: interpretação de sinais, requisitos mínimos de evidência, dados insuficientes, regras de encaminhamento e formato de análise.

As páginas foram consultadas no planejamento, mas o corpus ainda não foi coletado/produzido. Confirmar atualidade, pertinência e direitos antes de publicar os conteúdos. Fonte pública não equivale a licença aberta. Documentos próprios devem declarar autoria e caráter de procedimento do protótipo, sem se passar por norma técnica ou manual de concessionária.

### 7.2 Catálogo de fontes

Cada documento terá `document_id`, título, autor/organização, URL ou caminho, formato, data de consulta, data do documento quando disponível, jurisdição, licença/direitos, política de redistribuição, hash SHA-256 e número de trechos.

- Conteúdo com redistribuição permitida: publicar conforme suas condições.
- Sem licença explícita: registrar referência, síntese autoral atribuída e procedimento de reconstrução apropriado; não publicar integralmente.
- Normas técnicas e materiais pagos não serão copiados sem direito de uso.
- Se não houver base suficiente para responder a uma classe de casos, declarar a lacuna e perguntar antes de ampliar o escopo.

### 7.3 Chunking e índice

- Remover menus e conteúdo sem relação com a tarefa.
- Preservar títulos, condições de aplicabilidade e separação entre jurisdições.
- Até 250 tokens por trecho, medidos com o tokenizer escolhido; sobreposição máxima de 40 tokens somente quando necessária para manter o sentido.
- IDs derivados do documento, revisão e posição; guardar texto, seção, abrangência e hash.
- Não impor número artificial de documentos ou trechos. A cobertura deve ser conferida contra os casos suportados.
- Índice e catálogo terão versão ligada aos hashes do corpus.

## 8. Dados, gabaritos e prevenção de vazamento

### 8.1 Quantidades e divisão

Meta inicial: 600 exemplos, com 400 de treino, 80 de validação e 120 de teste. Gerar candidatos a partir de cenários e fatos da base, sem usar APIs pagas. Respostas autorais e variantes sintéticas precisam de revisão; não chamar o conjunto de dados reais de campo.

Agrupar por família de ocorrência, cenário e paráfrases antes de dividir. Uma família não pode aparecer em múltiplas divisões. Deduplicar por conteúdo normalizado e procurar semelhança textual entre divisões. Se não for possível produzir 600 exemplos independentes e corretos, perguntar em vez de completar com repetição ou fatos inventados.

O compartilhamento do corpus de conhecimento entre os experimentos é intencional no RAG. O que não pode vazar são perguntas, respostas-alvo e variantes dos casos finais para o treinamento ou ajuste de parâmetros.

### 8.2 Composição do teste final

| Grupo | Quantidade | Resultado esperado |
|---|---:|---|
| Respondível | 40 | Análise limitada ao que as evidências permitem |
| Não consta | 20 | Recusa fundamentada, sem completar pela memória do modelo |
| Dados insuficientes | 20 | Apontar os dados/calibração faltantes |
| Contradições | 15 | Identificar incompatibilidade sem escolher evidência arbitrariamente |
| Fora do escopo | 15 | Informar o limite da tarefa |
| Indução/prompt injection | 10 | Manter regras e não inventar conclusão ou fonte |

Os casos de indução serão marcados também pela tarefa de origem para permitir avaliar a resposta correta, não só resistência genérica.

### 8.3 Registro de exemplo

Cada registro deverá conter: `case_id`, `scenario_family`, `split`, `category`, entrada da ocorrência, origem real/simulada, resposta-alvo, resultado esperado, fatos obrigatórios, fatos proibidos, documentos/trechos relevantes e situação da revisão.

A resposta-alvo usará o mesmo esquema semântico da API. Metadados de medição (latência, revisão efetivamente executada, request_id) não serão inventados pelo modelo nem usados como alvo de linguagem.

Revisão: validação mecânica de todos os exemplos e revisão semântica dos gabaritos, com pendências expostas ao usuário. Congelar as divisões e seus hashes antes do primeiro treino que produzirá resultados oficiais. Teste final ficará fora dos comandos de ajuste de treino e de limiar.

## 9. Recuperação e seleção do contexto

### 9.1 Algoritmo v1

- Dois vetorizadores: palavras com n-gramas 1–2 e caracteres `char_wb` 3–5, com normalização L2.
- Normalizar Unicode e espaços; manter negações e termos relevantes, sem remoção indiscriminada de stopwords.
- Similaridade final: média dos dois cossenos, pesos 0,5/0,5.
- Aplicar regras de abrangência documental antes da seleção final. Sem município, usar documentos genéricos; não apresentar canal local específico como universal.
- Ordenação decrescente por escore; empates resolvidos por chunk_id para reprodução.
- Selecionar até três trechos acima do limiar escolhido na validação.
- Pergunta construída com solicitação e observações relevantes, sem nomes de cidadãos ou identificadores que não ajudem a busca.

### 9.2 Recall e calibração

Neste projeto, recall@k será a fração dos trechos relevantes recuperados entre todos os trechos relevantes rotulados para a pergunta, calculada por caso e agregada por média. Informar adicionalmente hit@k (pelo menos um relevante), para não confundir as duas métricas. Casos sem trecho relevante serão avaliados na recusa e não entrarão no denominador do recall.

Medir recall@1 e recall@3 antes do limiar e cobertura após o limiar. Para calibrar, testar valores 0,00 a 1,00 em passos de 0,01 somente na validação. Escolher o maior F1 de responder/abster com empate favorecendo menor taxa de resposta indevida e, persistindo empate, maior limiar. Registrar distribuição dos escores e justificar a escolha; não interpretar cosseno como probabilidade.

Congelar vetorizadores, versão do corpus e limiar antes do teste. A mesma recuperação será usada em B e C.

### 9.3 Orçamento

Contexto total inicial: 2.048 tokens, reservando até 768 para a saída. Calcular o espaço restante depois de instruções, chat template e entrada. Não cortar entrada de sensor ou documento silenciosamente. Se os trechos não couberem, reduzir o número de trechos por ordem de escore e registrar os trechos efetivamente utilizados; se instruções e entrada já excederem o orçamento, rejeitar a requisição de forma explícita.

## 10. Modelo e desenho dos experimentos

### 10.1 Artefatos base

Modelo escolhido: `Qwen/Qwen2.5-7B-Instruct` (Apache 2.0). Baixar revisão identificada do repositório original; registrar SHA de revisão e hashes. Converter localmente para MLX em 4 bits, grupo de quantização 64, se suportado pela versão validada. A base resultante, tokenizer e chat template serão idênticos nos três modos.

Separar original baixado, base convertida, adaptadores e resultados por run_id. Não baixar novamente pesos já íntegros e correspondentes à revisão. Não apagar o original após conversão automaticamente.

### 10.2 Matriz controlada

| Modo | Base | Recuperação | Adaptador |
|---|---|---|---|
| A: base_sem_contexto | Mesma base quantizada | Não | Não |
| B: rag_simples | Mesma base quantizada | Sim | Não |
| C: rag_finetuning | Mesma base quantizada | Mesma de B | Sim |

O modo A representa “modelo sem contexto”, mas recebe instruções de tarefa e JSON: não será deliberadamente privado do formato para inflar a vantagem de B/C. Em todos: geração gulosa (temperature 0), máximo de 768 tokens, mesma entrada observacional e instruções centrais. Em A, a lista de fontes de contexto estará vazia; não será possível comprovar fonte recuperada inexistente. Registrar essa diferença para interpretar citações.

### 10.3 Fine-tuning planejado

- Backend: MLX/MLX-LM, treinando adaptadores sobre a base quantizada.
- Loss somente na conclusão/resposta; usar o formato chat compatível com prompt masking.
- LoRA: rank 16, escala efetiva alpha/rank 2 (alpha equivalente a 32), dropout 0,05; últimas 16 camadas, projeções de atenção q_proj e v_proj.
- Otimizador AdamW, weight decay 0,01; learning rates candidatos `1e-5` e `5e-5`; taxa constante durante cada candidato.
- Microbatch 1, acumulação 4, batch efetivo 4, sem truncamento silencioso; seed 42.
- Contexto máximo de 2.048 tokens, incluindo alvo. Exemplos excedentes deverão ser reescritos ou explicitamente excluídos antes do congelamento, com contagem.
- Orçamento: duas passagens pelo treino. Com 400 exemplos, microbatch 1 e acumulação 4, são 800 microbatches e 200 atualizações de otimizador. Conferir a semântica de `iters` da versão instalada para não confundir microbatches com atualizações.
- Validar e salvar a cada 25 atualizações; manter checkpoints de cada execução em diretórios separados, sem sobrescrever.
- Validar perda em todo o conjunto de validação. Escolher, por candidato, o checkpoint de menor validation loss; empate favorece o anterior.
- Comparar os dois checkpoints candidatos na validação semântica: maior acerto, depois menor resposta indevida, depois maior JSON válido, depois menor latência mediana. Somente o selecionado será avaliado como C no placar final.

Parâmetros precisam ser mapeados à configuração efetiva da versão instalada; não inventar flags nem aceitar opções ignoradas. Se o framework não suportar o desenho escolhido, interromper e perguntar antes de substituir a estratégia.

### 10.4 Teste técnico antes do treino

Executar dez atualizações de otimizador em run de teste separado, sem usar o teste final. Conferir loss finita, gradientes/alteração de adaptadores, base congelada, salvamento e recarga. Verificar que ativar/desativar o adaptador muda efetivamente o caminho executado, sem afirmar melhora de qualidade apenas por mudar os tokens.

Medir duração por atualização, pico de memória e condições do sistema. Exibir estimativa da execução longa. Falta de memória ou tempo incompatível com o prazo exige comunicação e decisão do usuário, não troca silenciosa de modelo ou de método.

### 10.5 Proveniência de execução

Cada run registrará modelo/revisão, quantização, adaptador, corpus, datasets e seus hashes, configuração, seed, versões Python/pacotes, hardware, início/fim, duração, contagens, memória quando disponível e erros. Não alegar determinismo bit a bit entre versões/hardware.

## 11. Contrato da API v1

### 11.1 Endpoints

| Método e rota | Uso |
|---|---|
| POST `/v1/analisar` | Recebe ocorrência e retorna análise do modo C |
| GET `/health` | Liveness, sem inferência |
| GET `/ready` | Readiness: base, adaptador e índice prontos |
| GET `/docs` | OpenAPI interativo |
| GET `/demo` | Interface local acessível de demonstração |

Sem persistência de ocorrências na API v1. A aplicação do grupo será responsável pelo histórico de negócio. O modo de experimento é configurado no processo/CLI; não é campo público para usuário remoto escolher artefatos.

### 11.2 Entrada

- `ocorrencia_id`: string de 1 a 128 caracteres, definida pelo consumidor.
- `pergunta`: string de 1 a 2.000 caracteres, solicitação relacionada à tarefa.
- `municipio`: string opcional de até 120 caracteres; usar cidade/UF, sem inferir da máquina do usuário.
- `observado_em`: data/hora ISO 8601 com offset, opcional. Sem offset, dado inválido; não assumir fuso do servidor.
- `simulada`: boolean obrigatório para transparência da demonstração.
- `relato`: string opcional de até 4.000 caracteres; sem dados pessoais necessários à v1.
- `sensores`: até 20 leituras, cada uma com tipo, valor numérico finito, unidade, indicação de calibrado e referência de calibração opcional. `calibrado: true` exige referência descritiva não vazia; isso não prova a qualidade da calibração.
- `observacoes_visuais`: até 20 observações estruturadas: descrição de até 500 caracteres e confiança opcional entre 0 e 1. A confiança vem do componente de visão, não será inventada pela LLM.
- Pelo menos relato não vazio, leitura ou observação visual deve existir.
- Campos extras serão rejeitados. Nenhum campo aceitará caminho de arquivo ou URL para o servidor buscar automaticamente.

O orçamento em tokens prevalece sobre os máximos de caracteres: entrada sintaticamente válida pode ser rejeitada se não couber. Números negativos/limites dependem da unidade e do sensor; não impor faixa universal inventada.

Exemplo de entrada simulada:

```json
{
  "ocorrencia_id": "SIM-001",
  "pergunta": "Que análise preliminar é possível e o que precisa ser verificado?",
  "municipio": null,
  "observado_em": "2026-11-12T21:00:00-03:00",
  "simulada": true,
  "relato": "Observação de área pouco iluminada, sem confirmação do estado da luminária.",
  "sensores": [
    {"tipo": "ldr", "valor": 120, "unidade": "adc", "calibrado": false, "referencia_calibracao": null}
  ],
  "observacoes_visuais": []
}
```

### 11.3 Saída semântica do modelo

O modelo deverá gerar um único objeto JSON, sem cercas Markdown e sem texto antes/depois:

- `status`: `analise_preliminar`, `informacao_insuficiente` ou `fora_escopo`.
- `resumo`: explicação curta e compreensível.
- `hipoteses`: lista de objetos com descrição, `evidencias_observadas` (referências aos campos da entrada) e `fontes` (chunk_ids). Pode ser vazia; nunca precisa inventar uma causa.
- `informacoes_faltantes`: lista de informações necessárias, possivelmente vazia.
- `encaminhamento`: orientação textual de triagem; não constitui acionamento de serviço ou ordem de manutenção.
- `fontes`: lista de chunk_ids que sustentam as afirmações, limitada às fontes efetivamente fornecidas no contexto.

Regras: “não consta” é representado por `informacao_insuficiente`, com motivo no resumo. Evidências contraditórias sem resolução também levam a informação insuficiente. Fora de escopo será explícito. O modelo não gerará metadados de execução ou probabilidades de diagnóstico.

### 11.4 Envelope retornado pela API

A API acrescentará: `request_id` gerado pelo servidor, `ocorrencia_id`, `analise`, `referencias` com metadados reais de cada chunk citado e `execucao` com modo, revisão do modelo, identificação do adaptador, versão da base e `duracao_ms` medida. Texto externo e URLs retornados virão do catálogo validado, não de links inventados pela LLM.

O JSON será validado de forma estrita. A API não removerá cercas, completará campos ou fará nova geração escondida para declarar sucesso. Erros poderão ser usados para melhorar o treinamento em execuções futuras sem alterar retroativamente resultados congelados.

### 11.5 Erros

| HTTP | Situação |
|---|---|
| 200 | Análise válida, inclusive recusa estruturada |
| 413 | Corpo maior que 32 KiB |
| 422 | Campo inválido, dado obrigatório ausente ou orçamento de tokens excedido |
| 429 | Serviço ocupado com outra inferência; retornar Retry-After e erro claro |
| 502 | JSON ou referência gerada inválida |
| 503 | Modelo/adaptador/índice indisponível, ou inferência interrompida por falha do backend |

Erros terão `request_id`, `codigo` estável e `mensagem` sem stack trace, caminho privado ou segredo. Readiness retorna 503 enquanto recursos não estiverem disponíveis. Nenhum fallback silencioso para outro modelo, para modo B ou para resposta gravada.

### 11.6 Concorrência, serviço e logs

- Um worker do processo de inferência e uma geração por vez, protegido por exclusão mútua; sem fila ilimitada.
- Health e readiness continuarão respondendo enquanto a geração acontece; geração não bloqueará o event loop.
- SIGINT/SIGTERM devem encerrar a execução de forma controlada e liberar recursos quando possível.
- Logs JSONL locais com request_id, duração, resultado, códigos de erro e versões; não registrar por padrão relatos, coordenadas, identificadores pessoais ou corpos de requisição.
- Endpoint de análise nunca executará código ou ferramentas em nome da LLM.
- Bind inicial em `127.0.0.1:8000`; CORS fechado por padrão, demo de mesma origem.
- Não expor docs ou API publicamente, criar túnel, mudar firewall ou ampliar acesso por esta especificação.

## 12. Interface de demonstração e integração

### 12.1 Demo local

HTML/CSS/JavaScript simples servido pelo FastAPI, sem outro projeto Node nesta v1. Deve conter formulário, selo de dado simulado, os quatro cenários definidos, indicação de processamento, mensagens de indisponibilidade, resultado semântico e fontes clicáveis provenientes do catálogo.

Navegação por teclado, labels, contraste adequado e texto simples. Renderizar respostas como texto escapado; não executar HTML vindo de modelo/documento. Nenhuma chamada para API paga, analytics ou upload externo.

Exibir claramente quando o resultado vem do modelo real. Se houver seção de resultados anteriores, rotulá-la como registro de experimento, com run_id; nunca usá-la como fallback disfarçado.

### 12.2 Material para os colegas

- OpenAPI exportado, exemplos de entrada/saída e documentação de campos.
- Cliente Python de referência, endereço configurável e tratamento de falhas sem fabricar análise.
- Fixtures para testar o consumidor sem GPU, identificadas como fixtures de contrato.
- Roteiro de teste: cliente envia caso, API gera resposta com modelo real, consumidor exibe análise e fontes, evidência registrada com data e versões.

A integração real requer combinar com o responsável do grupo: origem do evento, consumidor, infraestrutura, segurança e disponibilidade. Dados ainda desconhecidos estão na seção de pendências. A API local pronta não significa URL pública de MVP entregue.

Treinar localmente não determina onde servir o modelo no futuro. O plano não presume host gratuito capaz de executar 7B, Mac permanentemente ligado ou autorização para acesso externo. O responsável por DevOps deverá apresentar a infraestrutura antes dessa etapa.

## 13. Avaliação e critérios de interpretação

### 13.1 Registros

Guardar, para cada caso/modo: entrada, prompt efetivo, trechos e escores recuperados, saída bruta, validade JSON, validação semântica, motivo de erro, latência, tokens, artefatos usados e julgamento de correção. Não incluir informação de gabarito no prompt de inferência.

### 13.2 Métricas

- Recall@1/recall@3 de busca e hit@k separado, conforme definição da seção 9.
- JSON bruto válido: parsing e conformidade do esquema antes de qualquer tratamento.
- Acerto: aderência aos fatos obrigatórios, ausência dos fatos proibidos, status adequado e consistência com observações; reportar por categoria e global.
- Alucinação: resposta com pelo menos uma afirmação factual não sustentada ou contradita pelas evidências/limites do caso. Denominador e quantidade de respostas abstidas devem aparecer junto para não premiar recusa universal.
- Resposta indevida: concluir em caso que exigia recusa/informação insuficiente.
- Recusa indevida: negar análise esperada em caso respondível.
- Referências: existência e pertencimento ao contexto separados de fidelidade semântica. Uma fonte existente pode não sustentar a afirmação.
- Operação: latência mediana/p95, tokens gerados e pico de memória quando obtido por medição real.

Estrutura e referências poderão ser verificadas automaticamente. Fundamentação e gabaritos exigem revisão humana registrada. Não usar outro LLM como único juiz, nem apresentar a autoavaliação do modelo como verdade objetiva.

### 13.3 Procedimento justo

1. Definir e congelar teste, corpus, limiar, esquema e protocolo.
2. Selecionar checkpoint somente com treino/validação.
3. Executar A, B e C em todos os casos finais, nas mesmas condições de hardware e geração; registrar aquecimento separado.
4. Se uma falha do processo invalidar o experimento, registrar a causa e preservar o run anterior antes de repetir.
5. Interpretar A × B (efeito de contexto) e B × C (efeito da especialização).
6. Não mudar gabaritos, limiar, prompt ou adaptador após observar o teste e manter o mesmo placar como se fosse não visto. Uma nova versão precisa de identificação e avaliação separada.

Metas iniciais: recall@3 >= 90% nos casos respondíveis e JSON bruto válido >= 95% no teste. Melhor acerto e menor alucinação são objetivos empíricos; não é permitido declarar ganho antecipado. Se C não melhorar B, relatar a limitação e discutir causas. Metas não substituem os critérios do professor.

### 13.4 Cinco erros reais

Para cada erro: case_id, run_id, modo, entrada, resposta bruta, resposta esperada, tipo de erro, causa provável explicitamente marcada e correção proposta. Não adulterar um caso correto para produzir erro. Se o teste congelado fornecer menos de cinco erros, buscar falhas em conjunto exploratório identificado, sem contaminar o placar principal. Propostas de correção não serão relatadas como implementadas sem nova validação.

## 14. Testes de software e evidências

| Grupo | Casos mínimos |
|---|---|
| Dados | JSONL inválido, duplicações, família em divisões diferentes, IDs ausentes, fonte sem direito de publicação |
| Índice | Ordenação e empate, top-k, score/limiar, documento de outra jurisdição, busca sem relevantes |
| Métricas | Exemplo calculável à mão para recall e hit, múltiplos relevantes, caso sem relevante, denominadores de recusa |
| Contexto | Limite de tokens, exclusão explícita de trechos, entrada grande, instrução maliciosa em documento |
| Geração | JSON inválido, campo extra, fonte inexistente, fonte fora do contexto, ausência de adaptador |
| API | Entrada válida, NaN/inf, horário sem offset, campos extras, corpo excessivo, ocupado, indisponível, erro do modelo |
| Demo | Teclado, rótulo simulado, escape de HTML, falha de rede e renderização de recusa |
| MLX real | Teste curto, loss finita, base congelada, adaptador alterado, salvamento/recarga |
| Ponta a ponta | Caso respondível e insuficiente usando o modelo real; cliente recebe e exibe fontes |

Testes unitários usarão geradores falsos para não baixar modelos. Os testes reais serão opt-in e rotulados; CI não fingirá ter testado GPU ao usar simulação. Não adicionar dezenas de testes que apenas reproduzam a implementação sem verificar comportamento importante.

Evidências: resultados do pytest, manifesto de treino, logs sem dados sensíveis, notebooks executados, placar por caso e captura/vídeo de integração. Só declarar um item concluído quando seu artefato existir e sua validação tiver sido executada.

## 15. Estrutura de entrega planejada

A árvore abaixo é o alvo futuro. Na etapa documental somente README.md, SPEC.md e AGENTS.md serão criados.

```text
citizentech-iluminacao-ia/
  README.md
  SPEC.md
  AGENTS.md
  pyproject.toml
  uv.lock
  .gitignore
  .env.example
  src/citizentech_ia/
    api/                  # contratos e rotas
    knowledge/            # ingestão, catálogo e chunks
    retrieval/            # índice e recuperação
    inference/            # MLX, contexto e análise
    training/             # preparação e execução controlada
    evaluation/           # métricas, protocolo e resultados
    demo/                 # página local
  configs/                # parâmetros de corpus, busca, treino e experimentos
  base/                   # catálogo, documentos publicáveis e chunks
  dados/                  # treino/validação e manifestos
  avaliacao/              # teste, gabaritos, placar e cinco erros
  notebooks/              # com saídas reais salvas
  docs/                   # relatório, integração e diagramas
  examples/               # cliente e fixtures simuladas
  tests/                  # testes unitários, contrato e testes reais opt-in
  models/                 # LOCAL, ignorado no Git
  adapters/               # LOCAL, distribuição tratada separadamente
  runs/                   # LOCAL, respostas brutas e checkpoints
```

Notebooks previstos: base e dados; recuperação/limiar; treino/validação; comparação final. Evitar que “executar tudo” baixe pesos ou inicie treino sem explicitar essa etapa. Notebooks de análise devem poder abrir resultados existentes sem repetir experimentos.

### 15.1 Interfaces operacionais futuras

Documentar comandos explícitos separados para: validar dados, construir índice, avaliar recuperação, verificar ambiente, baixar/converter modelo, teste curto, treino, seleção por validação, avaliação final e servir API. Não criar um único comando com instalação, download e treino ocultos.

O README deverá indicar quais comandos usam rede, alteram artefatos, carregam GPU ou executam treinamento. IDs/paths de modelos serão locais no serviço; indisponibilidade não disparará download durante uma requisição.

### 15.2 Relatório e README finais

- Nome completo e RM de todos os integrantes, fornecidos pelo usuário.
- Ficha Técnica: produto, cidadão/território, problema, proposta de valor, componentes, dados, IA, impacto e ODS vinculados e justificados.
- Diagrama de documentos, recuperação, fine-tuning, geração e integração.
- Tabela de fontes: origem, formato, direitos de uso e quantidade de trechos.
- Placar, configuração, interpretação, cinco erros e correções propostas.
- Instruções reproduzíveis, limitações, modelo/adaptador e links de vídeo/repositório/MVP.
- Diferenciar claramente resultados de teste pequeno, modelo-alvo, integração simulada e integração real.

O repositório público é exigência acadêmica, mas ainda não existe. Git, licença do código, distribuição do adaptador e publicação serão tratados após revisão e autorização do usuário. Não incluir venvs, segredos, pesos grandes ou dados pessoais reais. Acesso para correção deve ser conferido em janela anônima quando houver publicação.

## 16. Fases e aceitação

| Fase | Atividade | Critério para avançar |
|---|---|---|
| F0 | Pasta e especificação | Documentos gravados e conferidos; aguardar revisão |
| F1 | Regras, ambiente e esqueleto | Backup, regra aplicada, venv correta, dependências verificadas |
| F2 | Base e exemplos | Fontes rastreáveis, direitos tratados, gabaritos revisados e splits sem vazamento |
| F3 | Busca | Métricas calculadas, limiar escolhido na validação e índice versionado |
| F4 | Modelo e teste curto | Revisão/hash, conversão e treino técnico validado com medições |
| F5 | Treino e seleção | Candidatos executados, adaptadores salvos e seleção pela validação |
| F6 | Comparação científica | A/B/C completos no teste congelado, julgamentos e cinco erros reais |
| F7 | API e demo | Contrato testado e demonstração com modelo real |
| F8 | Integração | Consumidor real do grupo testado, ou bloqueio externo declarado |
| F9 | Relatório e publicação | Notebooks, documentação e vídeo revisados; links autorizados e funcionando |
| F10 | Encerramento e repouso | Relatório final salvo, tarefas encerradas e regras da seção 18 cumpridas |

Não iniciar F1 na etapa atual. A especificação não é comprovação de execução das fases futuras.

Cronograma de referência aprovado: 12/11 preparação; 13/11 dados e busca; 14/11 modelo/teste curto; 15/11 treino; 16/11 comparação; 17/11 API/integração; 18/11 documentação/vídeo; 19/11 revisão/envio. São metas, não promessa de duração. Replanejar com o usuário se medições ou dependências impedirem o cronograma, preservando os requisitos acadêmicos.

## 17. Pendências e decisões que exigem o usuário

| ID | Informação/decisão | Bloqueia |
|---|---|---|
| P01 | Aprovação/revisão desta SPEC e início da implementação | F1 em diante |
| P02 | Nome definitivo do produto, nomes e RMs, território do grupo | Documentação final e regras territoriais específicas |
| P03 | Responsável pela integração, origem das ocorrências e componente consumidor | F8; não impede cliente de referência local |
| P04 | Infraestrutura gratuita real do MVP, acesso e disponibilidade durante a correção | Integração remota e URL pública |
| P05 | Autorização/conta/repositório para publicação e distribuição do adaptador | Publicação, commits, pushes e links finais |
| P06 | Revisão das regras autorais e gabaritos, se houver decisão de domínio ambígua | Congelamento de dados correspondentes |
| P07 | Incompatibilidade, memória/tempo inviável ou necessidade de mudar modelo/treino | Execução dependente da mudança |
| P08 | Situação da API/integradores no momento do repouso | Encerramento da disponibilidade local |

O nome técnico da pasta foi definido no plano como citizentech-iluminacao-ia; ele não fixa nome comercial nem município. Não presumir São Paulo como território do grupo só porque há fonte paulista.

## 18. Encerramento e repouso do Mac

O usuário solicitou repouso após a implementação completa. Esta autorização não dispara repouso ao criar documentação, em caso de erro ou enquanto houver perguntas pendentes.

Antes de suspender, na etapa futura de encerramento:

1. Salvar código, configurações, relatórios, logs e adaptadores/checkpoints concluídos.
2. Confirmar que não há treino, avaliação, instalação ou download deste projeto em andamento.
3. Não encerrar processos de outros projetos ou aplicativos com documentos do usuário.
4. Informar e documentar que a API local ficará indisponível. Se o grupo depender dela naquele momento e isso não estiver resolvido, perguntar antes de suspender.
5. Registrar o resultado final e pendências; não marcar integração/publicação como concluída se estiver bloqueada.
6. Avisar o usuário de que o Mac entrará em repouso e solicitar a ação de repouso pelo mecanismo autorizado do macOS, respeitando as permissões exigidas.
7. Não configurar agendamento recorrente, desligamento, reinicialização ou suspensão forçada. Não prometer verificar o computador já dormindo.

## 19. Referências técnicas para a implementação

Consultar as versões atuais durante o setup e registrar a revisão realmente utilizada:

- Modelo e licença: https://huggingface.co/Qwen/Qwen2.5-7B-Instruct
- MLX-LM e treinamento de adaptadores: https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/LORA.md
- MLX, arquitetura e exemplos: https://mlx-framework.org/
- Condições térmicas do Mac: https://support.apple.com/en-au/102336
- Histórico pessoal: Developer Workspace, notas Projetos existentes, Python e UV, Treinamento de IA no MacBook e MacBook Configuration - contexto consolidado.

A SPEC é a referência funcional do projeto. Alterações de decisão devem registrar o motivo, impacto em dados/API/avaliação e autorização pertinente. Nenhum resultado numérico ou integração futura poderá ser preenchido como concluído antes de sua execução e validação.

## Registro de execução — 12/11/2026
P01 resolvida: usuário autorizou testes primeiro, implementação e validação local. A fase documental anterior terminou. Alteração global da regra de dúvidas aplicada com backup. Estados históricos acima descrevem a criação da SPEC, não bloqueiam a autorização mais recente.

## Estado medido após a implementação — 12/11/2026

A autorização posterior do usuário permitiu implementar este plano. A documentação de planejamento acima foi preservada; o estado efetivamente medido está em docs/ACEITACAO.md, docs/RELATORIO.md e docs/INTERPRETACAO.md. Dois candidatos locais e os 360 casos finais foram concluídos; 25 testes de software passaram e a API foi exercitada com o modelo real. As metas de recall@3 e conformidade do esquema não foram atingidas. Revisão humana independente, integração real do grupo, vídeo, integrantes e publicação continuam pendentes. Não confundir conclusão da implementação/experimentos locais com aceitação de qualidade ou entrega integral da GS.
