"""Ponte HTTP da mesma instância de nuvem para a fila GPU, preservando /v1/analisar."""

import logging
import uuid
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from starlette.concurrency import run_in_threadpool

from ..schemas import AnalysisResponse, ErrorResponse, Occurrence

logger = logging.getLogger("citizentech.cloud")


def create_proxy_app(predict, ready, page):
    app = FastAPI(title="CitizenTech Iluminação IA — nuvem", version="1.0.0")
    app.state.busy = False

    def error(request, status, code, message, headers=None):
        body = {"request_id": request.state.rid, "codigo": code, "mensagem": message}
        return JSONResponse(body, status_code=status, headers=headers)

    @app.middleware("http")
    async def limit(request, call_next):
        request.state.rid = str(uuid.uuid4())
        size, parts = 0, []
        async for part in request.stream():
            size += len(part)
            if size > 32768:
                return error(request, 413, "corpo_excessivo", "Limite de 32 KiB excedido.")
            parts.append(part)
        request._body = b"".join(parts)
        response = await call_next(request)
        response.headers.setdefault("X-Request-ID", request.state.rid)
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        return error(request, 422, "entrada_invalida", "Confira os campos e as observações fictícias.")

    @app.get("/")
    def home():
        return RedirectResponse("/demo")

    @app.get("/demo", response_class=HTMLResponse)
    def demo():
        return Path(page).read_text()

    @app.get("/health")
    def health():
        return {"status": "ativo", "execucao": "nuvem"}

    @app.get("/ready")
    def readiness():
        return JSONResponse({"pronto": bool(ready())}, status_code=200 if ready() else 503)

    @app.post("/v1/analisar", response_model=AnalysisResponse)
    async def analyze(occurrence: Occurrence, request: Request):
        if not occurrence.simulada:
            return error(request, 422, "entrada_invalida", "Esta POC pública aceita apenas dados fictícios.")
        if not ready():
            return error(request, 503, "modelo_indisponivel", "Modelo em nuvem indisponível.")
        if app.state.busy:
            return error(request, 429, "ocupado", "Uma análise já está em andamento.", {"Retry-After": "5"})
        app.state.busy = True
        try:
            headers = {}
            if request.headers.get("x-ip-token"):
                headers["x-ip-token"] = request.headers["x-ip-token"]
            result = await run_in_threadpool(predict, occurrence.model_dump(mode="json"), headers)
            status = result["status_code"]
            if status == 200:
                body = AnalysisResponse.model_validate(result["body"]).model_dump(mode="json")
                if body["ocorrencia_id"] != occurrence.ocorrencia_id:
                    raise ValueError("Resposta de outra ocorrência.")
            elif status in {413, 422, 429, 502, 503}:
                body = ErrorResponse.model_validate(result["body"]).model_dump()
            else:
                raise ValueError("Status remoto inválido.")
            return JSONResponse(body, status_code=status, headers={"X-Request-ID": body["request_id"]})
        except Exception:  # noqa: BLE001 -- no provider errors, headers or payloads in public output
            logger.warning("Falha na fila GPU; request_id=%s", request.state.rid)
            return error(request, 503, "gpu_indisponivel",
                         "Não foi possível executar a análise na nuvem; pode haver fila ou limite de uso.")
        finally:
            app.state.busy = False

    return app
