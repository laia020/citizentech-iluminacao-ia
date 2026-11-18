"""Serviço revisado, com identificação dos pesos e política separados do histórico v2."""

import json
from pathlib import Path

from ..datasets import sha, verify_freeze
from ..service import ThreadBoundAnalyzer
from .inference import SYSTEM, ReviewedAnalyzer
from .pipeline import retriever


def local_service(root):
    root = Path(root).resolve()
    verify_freeze(root, system_prompt=SYSTEM)
    selection = json.loads((root / "configs/selected.json").read_text())
    adapter = root / selection["adapter_path"]
    if sha(adapter / "adapters.safetensors") != selection["adapter_sha"]:
        raise ValueError("Adaptador servido diverge da seleção registrada.")

    def factory():
        from ..inference import MLXGenerator

        return ReviewedAnalyzer(
            MLXGenerator(root / "models/qwen-7b-4bit", adapter, require_adapter=True),
            retriever(root),
            threshold=json.loads((root / "configs/retrieval.json").read_text())["threshold"],
        )

    return ThreadBoundAnalyzer(factory)


def create_reviewed_app(root):
    from ..api import create_app

    return create_app(local_service(root), demo_path=Path(__file__).with_name("demo.html"))
