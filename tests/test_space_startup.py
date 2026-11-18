"""Inicialização ZeroGPU explícita para a aplicação montada em FastAPI."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


def entrypoint():
    path = Path(__file__).resolve().parents[1] / "deploy/hf-space/app.py"
    spec = importlib.util.spec_from_file_location("space_entrypoint", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_mounted_app_reports_real_gpu_startup_and_refuses_inactive_provider():
    app = entrypoint()
    events = []
    app.report_startup(SimpleNamespace(startup=lambda: events.append("provider_startup")))
    assert events == ["provider_startup"]
    with pytest.raises(RuntimeError):
        app.report_startup(SimpleNamespace())


def test_entrypoint_does_not_start_server_on_user_machine(monkeypatch):
    monkeypatch.delenv("SPACE_ID", raising=False)
    with pytest.raises(SystemExit):
        entrypoint().main()
