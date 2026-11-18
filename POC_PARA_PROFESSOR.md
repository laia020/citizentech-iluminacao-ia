# POC1.5B para o professor

**Modelo realmente treinado localmente; cenários fictícios.** A tela permite escolher cinco exemplos ou escrever pergunta/observações livres. Fluxo real:tela→API→busca→Qwen1.5B+LoRA→JSON/referências→tela. Não há sensor físico,sistema municipal ou componentes dos colegas conectados; os registros da tela são marcados como simulados. Não existem respostas prontas de reserva.

Abrir <http://127.0.0.1:8000/demo> com o serviço ativo. Para iniciar na raiz do projeto:`.venv/bin/python scripts/servir_poc_validada.py`. Funciona apenas neste Mac acordado; publicação/URL externa é etapa distinta.

## Demonstração curta

1. Explicar o problema de triagem de iluminação pública e a geração de dados fictícios, sem apresentar como medição real ou laudo.
2. Mostrar observação noturna,leituraADC sem curva,custo não informado,conflito e ordem indevida no relato.
3. Deixar o professor editar pergunta/observações no cenário livre; conferir fontes e resposta completa.
4. Mostrar a comparação das mesmas30 perguntas emA/B/C,notebook com saídas e cinco erros/propostas. Destacar que estrutura,status e conteúdo são critérios diferentes.
5. Explicar as falhas remanescentes e o que ainda depende do produto do grupo/publicação.

## Resultado e limites

R1/400 passos eR2/800 foram treinados em8min36s e15min56s. R1 foi escolhido pela validação antes do teste. No teste30,C teve25 acertos semânticos,3 erros e2 incertos; alucinação confirmada em2 casos e incerta em2. A base sem contexto teve14 acertos,15 erros e1 incerto; alucinação confirmada em7 e incerta em2. São julgamentos técnicos por IA, sem revisão humana independente. A redução de alucinação foi observada, mas seu intervalo inclui zero; não afirmar prova conclusiva.

Os seis exemplos de API/POC retornaram200 com o modelo real. Quatro respostas foram plenamente adequadas nesta revisão; uma respostaADC/defeito ficou incompleta/ambígua e a pergunta de técnico teve citaçãoCPFL indevida, embora reconhecesse corretamente a ausência de documento. Não usar esses exemplos como taxa de qualidade geral nem esconder casos ruins. Evidências em `experimentos/v5-1.5b/docs/teste-poc-real.json` e `revisao-poc-conteudo.json`.

A inspeção visual/interação em navegador continua pendente, após recusa anterior de aprovação automática sem contorno. A interface teve sintaxe/ASGI conferidos e as chamadas de API usaram a LLM real.39 testes de software e notebook executado não substituem avaliação factual.

O PDF permite protótipo navegável/dados simulados documentados, mas mantém os artefatos de cada disciplina e produto comum/integrado. Integrantes/RMs/território,partes dos colegas,integração real,publicação e vídeo continuam pendentes. [Relatório atual](experimentos/v5-1.5b/docs/RELATORIO-1_5B.md).

## Visual Akona Energy

A tela da IA agora segue a identidade do MVP de DevOps indicado pelo usuário:logotipo,verdes,tipografiaManrope/Inter,cabeçalho,formulário e rodapé. Recarregue `http://127.0.0.1:8000/demo`. Os links externos levam ao MVP; a POC continua executando a IA local sem criar chamados na produção. Ver [registro da adaptação](experimentos/v5-1.5b/docs/FRONT-AKONA.md).39 testes aprovados e chamada realAPI conferida;inspeção visual no navegador pendente por indisponibilidade da ferramenta nesta sessão. Backup:`/Users/lucasmanentti/.codex/backups/citizentech-front-akona-20261117-222515`;restaurar pelo manifesto comparando/copiando o arquivo desejado ao caminho original.

## Citação não validada na demonstração

A versão atual inclui guarda limitada contra citações incompatíveis:CPFL/SP-Regula genéricos não sustentam designação de técnico,contrato/protocolo específico ou preço. O caso de técnico pode agora exibir erro `fonte_incompativel`,em vez de uma análise validada comCPFL. Mostrar o erro como falha detectada,nunca contá-lo como acerto de geração. Não houve retreinamento ou alteração da evidência de alucinação. [Registro e limites](experimentos/v6c-validacao/README.md).
