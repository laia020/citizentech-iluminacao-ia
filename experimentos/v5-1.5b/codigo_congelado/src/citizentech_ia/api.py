import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.concurrency import run_in_threadpool

from .inference import ContextOverflow, InvalidGeneration
from .schemas import AnalysisResponse, ErrorResponse, Occurrence

logger = logging.getLogger("citizentech.api")


def create_app(analyzer=None, demo_path=None):
    @asynccontextmanager
    async def lifespan(app):
        try:
            yield
        finally:
            current = app.state.analyzer
            if current is not None and hasattr(current, "close"):
                await run_in_threadpool(current.close)

    app = FastAPI(title="CitizenTech Iluminação IA", version="1.0.0", lifespan=lifespan)
    app.state.analyzer = analyzer
    app.state.busy = False

    def error(request, status, code, message, headers=None):
        return JSONResponse(
            status_code=status,
            content={"request_id": request.state.rid, "codigo": code, "mensagem": message},
            headers=headers,
        )

    @app.middleware("http")
    async def guard(request: Request, call_next):
        request.state.rid = str(uuid.uuid4())
        size, parts = 0, []
        async for part in request.stream():
            size += len(part)
            if size > 32768:
                return error(request, 413, "corpo_excessivo", "Limite de 32 KiB excedido.")
            parts.append(part)
        request._body = b"".join(parts)
        start = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.rid
        logger.info(
            json.dumps(
                {
                    "request_id": request.state.rid,
                    "status": response.status_code,
                    "duration_ms": round((time.perf_counter() - start) * 1000),
                }
            )
        )
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_input(request, exc):
        return error(
            request,
            422,
            "entrada_invalida",
            "Confira campos, evidências, números finitos e offset da data/hora.",
        )

    @app.get("/health")
    def health():
        return {"status": "ativo"}

    @app.get("/ready")
    def ready():
        available = app.state.analyzer is not None and app.state.analyzer.generator.ready
        return JSONResponse({"pronto": bool(available)}, status_code=200 if available else 503)

    @app.post(
        "/v1/analisar",
        response_model=AnalysisResponse,
        responses={status: {"model": ErrorResponse} for status in [413, 422, 429, 502, 503]},
    )
    async def analyze(occurrence: Occurrence, request: Request):
        a = app.state.analyzer
        if a is None or not a.generator.ready:
            return error(request, 503, "modelo_indisponivel", "Base, índice ou adaptador indisponível.")
        # No await occurs between check/set: all route calls use the same event loop.
        if app.state.busy:
            return error(request, 429, "ocupado", "Uma análise já está em andamento.", {"Retry-After": "5"})
        app.state.busy = True
        start = time.perf_counter()
        try:
            result = await run_in_threadpool(a.analyze, occurrence)
            refs = set(result["analysis"].fontes)
            return {
                "request_id": request.state.rid,
                "ocorrencia_id": occurrence.ocorrencia_id,
                "analise": result["analysis"].model_dump(),
                "referencias": [
                    {k: c.get(k) for k in ["chunk_id", "document_id", "title", "url"]}
                    for c in result["chunks"]
                    if c["chunk_id"] in refs
                ],
                "execucao": {
                    **a.generator.metadata(),
                    "modo": a.mode,
                    "versao_base": a.base_version,
                    "duracao_ms": round((time.perf_counter() - start) * 1000),
                },
            }
        except ContextOverflow:
            return error(
                request, 422, "contexto_excedido", "Entrada excede o orçamento de tokens; reduza o relato."
            )
        except InvalidGeneration:
            return error(
                request, 502, "geracao_invalida", "O modelo não produziu uma análise estruturalmente válida."
            )
        except Exception:  # noqa: BLE001 -- isolate backend faults from public error responses
            logger.error(json.dumps({"request_id": request.state.rid, "codigo": "falha_backend"}))
            return error(
                request, 503, "falha_backend", "Inferência interrompida; consulte o responsável pelo serviço."
            )
        finally:
            app.state.busy = False

    @app.get("/demo", response_class=HTMLResponse)
    def demo():
        return (Path(demo_path) if demo_path else Path(__file__).parent / "demo.html").read_text()

    return app
