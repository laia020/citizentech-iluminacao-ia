# Adendo de auditoria anterior à geração

A conferência adicional identificou sobreposições semânticas que a deduplicação literal e os IDs de família não detectavam. O plano de exclusão foi gravado e hasheado antes de existir qualquer resposta de validação/teste v3. Não houve exclusão por desempenho observado. Os arquivos de dados e o protocolo original permanecem preservados.

O conjunto bruto continua com 80 casos de validação e 120 de teste. A parte confirmatória terá 64 casos/16 famílias na validação e 112 casos/28 famílias no teste, após retirar os grupos identificados em configs/clean_holdout_plan.json. Ambos os placares, completo e sem sobreposição identificada, serão publicados. As frases originais e motivos de cada exclusão podem ser auditados. Não se afirma independência semântica perfeita nem generalização para campo.

O treino em andamento usa apenas os 400 exemplos de treino para gradientes. A validação de loss original é diagnóstica, sem ajustar a programação fixa de 800 microsteps e taxa constante. Em vez de selecionar seu melhor checkpoint, serão usados os pesos finais de exatamente 800 passos e a seleção entre candidatos será feita somente com geração na parte limpa da validação. Assim, não é necessário apagar ou fingir um novo treinamento: os pesos são preservados e sua origem fica explícita. A condição predefinida para um segundo candidato passa a ser calculada nesses 64 casos, antes de abrir o teste.

Esse adendo substitui apenas a referência ao melhor checkpoint de loss e delimita os conjuntos de análise. Não altera entrada, alvo, corpus, prompt, política de geração nem respostas após observar o teste. Os parâmetros e julgamentos continuam sujeitos às limitações da avaliação técnica por IA.

A calibração de busca já realizada usa os 80 casos originais como conjunto de desenvolvimento. Seu recall de 95% não é estimativa de teste ou validação externa. O adendo não foi usado para recalibrar esse limiar; a recuperação será medida novamente nas perguntas finais e no subconjunto confirmatório declarado.
