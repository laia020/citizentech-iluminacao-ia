---
title: Akona Energy - CitizenTech IA
emoji: 💡
colorFrom: green
colorTo: gray
sdk: gradio
sdk_version: 6.32.0
python_version: '3.12'
app_file: app.py
pinned: false
models:
  - Qwen/Qwen2.5-1.5B-Instruct
---

# Akona Energy — CitizenTech Iluminação IA

POC de triagem de iluminação pública, com dados fictícios, RAG e Qwen2.5-1.5B-Instruct especializado por LoRA. Treinamento realizado localmente; inferência desta aplicação executada na nuvem, independente do Mac do autor.

O adaptador r1 é o mesmo selecionado antes do teste, carregado diretamente do pacote original verificado por SHA-256. Não há novo treinamento, fusão ou quantização. O backend PyTorch implementa a operação LoRA original; diferenças numéricas entre plataformas podem afetar respostas. Resultados do experimento MLX histórico não são automaticamente resultados desta hospedagem.

- [Código, equipe, ficha técnica, relatório e evidências](https://github.com/laia020/citizentech-iluminacao-ia).
- Tela: `/demo`; contrato HTTP: `/docs`; prontidão: `/ready`; análise: `POST /v1/analisar`.
- Endpoint Gradio `/analisar`: recebe o mesmo objeto de ocorrência e retorna `status_code` e `body`.
- Use somente ocorrências fictícias com `simulada: true`. Confira fontes e limites; não é diagnóstico elétrico.
- A proteção limitada de citações e as validações são preservadas. Erros e indisponibilidade são explícitos, sem resposta gravada de reserva.
- ZeroGPU tem filas e cotas. O modelo pode estar carregado e a inferência ainda ser impedida pela cota; não há promessa de disponibilidade contínua.
- O loopback usado pela ponte da fila é interno à instância de nuvem; não há túnel para o computador pessoal.

A base é Apache-2.0, com cópia da licença no pacote do adaptador. A licença dos materiais autorais do projeto não foi definida automaticamente. A conexão com o produto dos colegas é uma etapa distinta; identidade visual comum não comprova integração.
