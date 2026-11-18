"""Bloqueio limitado de incompatibilidades conhecidas; não prova suporte semântico geral."""

import json
import logging
import re
import unicodedata

from fastapi.responses import JSONResponse, Response

GENERIC_INSTITUTIONAL_SOURCES = {"cpfl-reparos:1", "sp-faq:1"}
logger = logging.getLogger("citizentech.citation_guard")


def incompatible_citations(question, citations):
    text = "".join(
        c for c in unicodedata.normalize("NFKD", question.lower()) if not unicodedata.combining(c)
    )
    # Estes dois trechos descrevem serviços/abrangência, nunca registros operacionais do caso.
    assignment = re.search(r"\b(tecnico|tecnica|profissional|eletricista|equipe|funcionario|empresa)\b", text)
    assignment = assignment and re.search(
        r"\b(designad\w*|escalad\w*|despachad\w*|encarregad\w*|responsavel|executora|enviad\w*)\b", text
    )
    missing_document = re.search(r"\b(contrato|contratual|garantia|protocolo)\b", text)
    missing_document = missing_document or (
        "ordem de servico" in text and re.search(r"\b(numero|codigo|identificador)\b", text)
    )
    exact_cost = re.search(r"\b(preco|custo|custa|custara|cobrado|cobrar|pagar|cobranca|orcamento)\b", text)
    if not (assignment or missing_document or exact_cost):
        return []
    return sorted(set(citations) & GENERIC_INSTITUTIONAL_SOURCES)


def attach_guard(app):
    @app.middleware("http")
    async def citation_support_guard(request, call_next):
        if request.method != "POST" or request.url.path != "/v1/analisar":
            return await call_next(request)
        # Enforce the same body limit before buffering. Starlette replays the cached body downstream.
        parts, size = [], 0
        async for part in request.stream():
            size += len(part)
            if size > 32768:
                import uuid

                rid = str(uuid.uuid4())
                return JSONResponse(status_code=413, headers={"X-Request-ID": rid}, content={
                    "request_id": rid, "codigo": "corpo_excessivo", "mensagem": "Limite de 32 KiB excedido.",
                })
            parts.append(part)
        raw_body = b"".join(parts)
        request._body = raw_body
        try:
            payload = json.loads(raw_body)
        except (ValueError, UnicodeError):
            return await call_next(request)
        response = await call_next(request)
        if response.status_code != 200:
            return response
        body = b"".join([part async for part in response.body_iterator])
        result = json.loads(body)
        citations = list(result["analise"]["fontes"])
        for hypothesis in result["analise"]["hipoteses"]:
            citations.extend(hypothesis["fontes"])
        blocked = incompatible_citations(payload.get("pergunta", ""), citations)
        if blocked:
            rid = result["request_id"]
            logger.info(json.dumps({"request_id": rid, "status": 502, "codigo": "fonte_incompativel"}))
            return JSONResponse(status_code=502, headers={"X-Request-ID": rid}, content={
                "request_id": rid, "codigo": "fonte_incompativel",
                "mensagem": "A fonte citada não contém o dado operacional solicitado. "
                            "A análise não foi validada; confira a documentação pertinente com uma pessoa.",
            })
        return Response(content=body, status_code=200, headers=dict(response.headers), media_type=response.media_type)

    return app
