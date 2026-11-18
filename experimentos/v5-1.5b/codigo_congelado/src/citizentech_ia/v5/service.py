"""POC disponível sem executar a LLM enquanto não houver adaptador selecionado."""

import json
from pathlib import Path

from ..api import create_app
from ..datasets import sha, verify_freeze
from ..service import ThreadBoundAnalyzer
from .inference import SYSTEM, Analyzer, Generator
from .pipeline import retriever


def create_model_app(root):
    root = Path(root).resolve()
    page = Path(__file__).with_name("demo.html")
    if not (root / "configs/selected.json").exists():
        return create_app(None, demo_path=page)
    verify_freeze(root, system_prompt=SYSTEM)
    config = json.loads((root / "configs/model.json").read_text())
    selected = json.loads((root / "configs/selected.json").read_text())
    adapter = root / selected["adapter_path"]
    if sha(adapter / "adapters.safetensors") != selected["adapter_sha"]:
        raise ValueError("Adaptador diverge da seleção registrada.")

    def factory():
        generator = Generator(root / config["model_path"], adapter)
        if generator.metadata()["modelo"] != config["model"]:
            raise ValueError("Modelo local diverge da configuração.")
        return Analyzer(
            generator,
            retriever(root),
            threshold=json.loads((root / "configs/retrieval.json").read_text())["threshold"],
        )

    return create_app(ThreadBoundAnalyzer(factory), demo_path=page)
