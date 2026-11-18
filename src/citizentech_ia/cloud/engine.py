"""Usa as mesmas validações da API original também no endpoint público Gradio."""

import uuid

from fastapi.testclient import TestClient

from ..api import create_app
from ..citation_guard import attach_guard
from ..schemas import Occurrence


class CloudEngine:
    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.app = attach_guard(create_app(analyzer))

    def __call__(self, value):
        try:
            occurrence = Occurrence.model_validate(value)
            if not occurrence.simulada:
                raise ValueError("POC pública aceita somente dados fictícios.")
        except ValueError:
            return {"status_code": 422, "body": {"request_id": str(uuid.uuid4()),
                    "codigo": "entrada_invalida", "mensagem": "Confira os campos e use apenas dados fictícios."}}
        # In-process ASGI only: no socket, local server or dependency on the user's Mac.
        with TestClient(self.app) as client:
            response = client.post("/v1/analisar", json=occurrence.model_dump(mode="json"))
        return {"status_code": response.status_code, "body": response.json()}
