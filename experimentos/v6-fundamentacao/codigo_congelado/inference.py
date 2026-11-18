import json

from ..inference import ContextOverflow
from ..v3.inference import ReviewedAnalyzer, SYSTEM as BASE_SYSTEM
from ..v3.retrieval import ReviewedRetriever, query

SYSTEM = BASE_SYSTEM + """
Conferência da resposta: responda à pergunta específica, inclusive quando ela tem duas partes.
Perguntas sobre preço, contrato, protocolo, garantia, equipe ou técnico de uma ocorrência pública
pertencem ao domínio: sem documento que forneça o dado, use informacao_insuficiente, não fora_escopo.
Ausência do documento não prova ausência do serviço, da equipe, da garantia ou do protocolo.
Pergunta legítima sobre limite de medição não é ordem maliciosa. Preserve a unidade já recebida.
Para citar, confira o que o trecho efetivamente diz. Um texto de canal de atendimento não comprova
designação de técnico ou preço. Cite somente o apoio à afirmação feita; sem apoio pertinente use [].
"""


def retriever(chunks):
    return ReviewedRetriever(chunks)


class GroundedAnalyzer(ReviewedAnalyzer):
    def prepare(self, occurrence):
        chunks = [] if self.mode == "base_sem_contexto" else self.retriever.search(
            query(occurrence), municipality=occurrence.municipio, threshold=self.threshold
        )
        while True:
            messages = [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": json.dumps({
                    "OCORRENCIA": occurrence.model_dump(mode="json", exclude={"ocorrencia_id"}),
                    "CONTEXTO": [{"chunk_id": c["chunk_id"], "texto": c["text"]} for c in chunks],
                }, ensure_ascii=False)},
            ]
            count = self.generator.count_messages(messages) if hasattr(self.generator, "count_messages") else (
                self.generator.count_tokens(json.dumps(messages, ensure_ascii=False))
            )
            if count + self.max_output <= self.context_limit:
                return messages, chunks, count
            if not chunks:
                raise ContextOverflow("Entrada excede contexto; não foi truncada.")
            chunks.pop()
