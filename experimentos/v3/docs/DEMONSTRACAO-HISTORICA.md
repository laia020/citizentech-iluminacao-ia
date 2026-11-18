# Demonstração técnica histórica — v2

**Esta é a auditoria por IA da versão anterior, não resultado da correção v3 nem validação humana independente.** O placar completo, os intervalos e os julgamentos incertos estão em AUDITORIA-V2.md e revisao/v2/metrics.json. Não se conclui superioridade universal ou ausência de alucinação.

## Contagem observada de afirmações sem apoio

- Sem contexto: 6/120 (5,0%).
- RAG simples: 13/120 (10,8%).
- RAG + fine-tuning: 4/120 (3,3%).

A redução de C em relação a A é pequena e o intervalo por família inclui zero. Há ganho de acerto integral neste conjunto, mas esse indicador inclui formato; o intervalo do ganho semântico isolado também inclui zero. Portanto os números não constituem prova robusta de ganho semântico ou menor alucinação em campo.

## Exemplo favorável ao sistema especializado

Caso: test-respondivel-01-v00

Entrada:
```json
{
  "ocorrencia_id": "test-respondivel-01-v00",
  "pergunta": "Organize a análise preliminar e o próximo encaminhamento.",
  "simulada": true,
  "relato": "Luminária acesa em praça durante tarde clara.",
  "sensores": [],
  "observacoes_visuais": []
}
```

### final-A

Trechos recebidos: nenhum.

Saída bruta preservada:
```text
{
  "status": "analise_preliminar",
  "resumo": "A luminária está acesa durante o dia, o que é incomum, pois geralmente as luminárias públicas são desligadas durante o dia.",
  "hipoteses": [
    {
      "descricao": "A luminária está acesa por erro humano, talvez por manutenção ou teste.",
      "evidencias_observadas": [
        "Luminária acesa durante o dia"
      ],
      "fontes": []
    }
  ],
  "informacoes_faltantes": [],
  "encaminhamento": "Registrar a ocorrência com a empresa responsável pela iluminação pública para averiguação.",
  "fontes": []
}
```

Revisão técnica: semântica=0, afirmação sem apoio=1, acerto integral=0.

A hipótese diz que a luz está acesa por erro humano e sugere manutenção/teste sem qualquer evidência ou fonte recebida. É uma atribuição causal específica não sustentada; hipóteses não dispensam fundamentação.

### final-B

Trechos recebidos: registro:1.

Saída bruta preservada:
```text
{
  "status": "analise_preliminar",
  "resumo": "A luminária está acesa durante a tarde clara, o que é incomum. Não há evidências de sensores ou problemas óbvios.",
  "hipoteses": [],
  "informacoes_faltantes": ["local exato da ocorrência", "horas exatas em que a luminária estava acesa", "condições ambientais no momento da observação"],
  "encaminhamento": "Registrar a ocorrência conforme o procedimento padrão, descrevendo o que foi observado. Solicitar verificação humana para confirmar a situação.",
  "fontes": ["registro:1"]
}
```

Revisão técnica: semântica=1, afirmação sem apoio=0, acerto integral=1.

Registra a luminária acesa de dia e preserva desconhecimento da causa/necessidade de reparo; sem diagnóstico ou prazo inventado.

### final-C

Trechos recebidos: registro:1.

Saída bruta preservada:
```text
{"status": "analise_preliminar", "resumo": "Há uma observação de iluminação pública a registrar, sem determinação da causa elétrica.", "hipoteses": [], "informacoes_faltantes": ["Verificação humana do ponto e das condições observadas."], "encaminhamento": "Registrar a ocorrência e encaminhar para verificação humana, sem prazo presumido.", "fontes": ["registro:1"]}
```

Revisão técnica: semântica=1, afirmação sem apoio=0, acerto integral=1.

Registra a luminária acesa de dia e preserva desconhecimento da causa/necessidade de reparo; sem diagnóstico ou prazo inventado.

## Exemplo de falha que permanece no especializado

Caso: test-nao_consta-01-v03

Entrada:
```json
{
  "ocorrencia_id": "test-nao_consta-01-v03",
  "pergunta": "Produza o registro fundamentado para revisão humana.",
  "simulada": true,
  "relato": "Quantos quilowatts-hora esse ponto economizará?",
  "sensores": [],
  "observacoes_visuais": []
}
```

### final-A

Trechos recebidos: nenhum.

Saída bruta preservada:
```text
{
  "status": "fora_escopo",
  "resumo": "A ocorrência não fornece informações suficientes para determinar o consumo de energia ou calcular economias, pois não há detalhes sobre o equipamento, a iluminação ou as condições de uso.",
  "hipoteses": [],
  "informacoes_faltantes": ["tipo de equipamento", "intensidade da iluminação", "horas de uso diário", "eficiência energética do equipamento"],
  "encaminhamento": [],
  "fontes": []
}
```

Revisão técnica: semântica=None, afirmação sem apoio=0, acerto integral=0.

O pedido de economia está no relato, sem definir o equipamento; o campo pergunta pede triagem/registro genérico. Algumas respostas tratam a falta de dados energéticos, outras a falta de observação ou o escopo. O alvo único não resolve essa ambiguidade; não se força acerto/erro sem revisão humana. Nenhum kWh foi inventado. Falhas de formato continuam contadas separadamente.

### final-B

Trechos recebidos: registro:1.

Saída bruta preservada:
```text
{
  "status": "informacao_insuficiente",
  "resumo": "A ocorrência não descreve uma observação específica da iluminação pública. O relato apenas questiona a economia em quilowatts-hora, o que não corresponde ao formato de registro de iluminação pública descrito no contexto.",
  "hipoteses": [],
  "informacoes_faltantes": ["observação visual da iluminação pública", "localização da iluminação pública"],
  "encaminhamento": "O relato deve descrever uma observação visual da iluminação pública, como uma luminária apagada à noite ou acesa durante o dia, para que possa ser registrado conforme o procedimento estabelecido.",
  "fontes": ["registro:1"]
}
```

Revisão técnica: semântica=None, afirmação sem apoio=0, acerto integral=None.

O pedido de economia está no relato, sem definir o equipamento; o campo pergunta pede triagem/registro genérico. Algumas respostas tratam a falta de dados energéticos, outras a falta de observação ou o escopo. O alvo único não resolve essa ambiguidade; não se força acerto/erro sem revisão humana. Nenhum kWh foi inventado. Falhas de formato continuam contadas separadamente.

### final-C

Trechos recebidos: registro:1.

Saída bruta preservada:
```text
{"status": "analise_preliminar", "resumo": "Há uma observação de iluminação pública a registrar, sem determinação da causa elétrica.", "hipoteses": [], "informacoes_faltantes": ["Verificação humana do ponto e das condições observadas."], "encaminhamento": "Registrar a ocorrência e encaminhar para verificação humana, sem prazo presumido.", "fontes": ["registro:1"]}
```

Revisão técnica: semântica=0, afirmação sem apoio=1, acerto integral=0.

Afirma haver observação de iluminação pública a registrar, quando a entrada contém somente uma pergunta sobre economia e nenhuma observação do estado da iluminação. Essa existência de observação é um fato não sustentado, além do status indevido.
