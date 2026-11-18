# Identidade Akona Energy na POC de IA

Alteração solicitada pelo usuário em17/11/2026:seguir o front do MVP de DevOps em https://ca-akona-energy-prod.salmoncoast-770d275b.eastus2.azurecontainerapps.io/. Consultados início,formulário público e folha de estilos porGET,somente leitura; nenhum chamado ou alteração foi enviado ao site de produção.

Aplicado à POC local:logotipoAkona da referência,cores #0f3d2e/#1b6b4a/#3fa66b,menta,branco/nevoa,fontesManrope/Inter,cabeçalho,hero,formulário,botões,bordas e rodapé. Fontes incorporadas na página local,sem depender deCDN. No computador,formulário e resultado ficam lado a lado;CSS adapta para uma coluna abaixo de820px. Links para o MVP de DevOps são externos e identificados; a tela local não cria chamados nem comprova integração com a fila de produção. Não foram transportadas promessas de prazo,SLA ou dados municipais para o comportamento da IA.

Arquivo alterado:`src/citizentech_ia/v5/demo.html`. JavaScript,cinco exemplos,contratoAPI,pipeline,prompt,pesos e dados preservados exatamente. Sem treinamento novo,instalação,commit,push ou deploy. O serviço existente entrega a nova página ao recarregar `http://127.0.0.1:8000/demo`.

Validação:39 testes de software aprovados em1,21s,sintaxeJS,IDs/âncorasHTML,igualdade da página servida,hashes dos fontes preditivos e fluxoDOM simulado (pronto/indisponível,envio,resultado,erro,limpeza,cenário livre). Uma requisição real simulada ao modelo1.5B foi registrada em teste-api-front-akona.json,comSHA do adaptador correspondente à seleção. TesteDOM simulado não equivale a navegador. O acesso ao navegador local está indisponível nesta sessão;inspeção visual real não foi realizada e continua pendente,sem contorno da recusa anterior.

Evidências:`validacao-front-akona.json`,`teste-api-front-akona.json`;HTML/CSS públicos e procedência em referencia-front-akona. Os registros científicos anteriores permanecem históricos comSHA da interface daquela execução; o novoSHA está na verificação de front,sem reescrever o relatório científico ou as respostas do teste.

Backup antes das alterações:`/Users/lucasmanentti/.codex/backups/citizentech-front-akona-20261117-222515`,com manifesto de caminhos. Restauração:comparar o arquivo desejado e copiá-lo de volta ao caminho original indicado no manifesto,preservando alterações posteriores. Não remover pesos,ambientes ou resultados. Regras globais preservadas.
