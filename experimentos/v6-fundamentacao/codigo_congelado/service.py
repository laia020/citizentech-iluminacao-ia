import json
from pathlib import Path

from ..api import create_app
from ..datasets import read_jsonl, sha
from ..service import ThreadBoundAnalyzer
from ..v5.inference import Generator
from ..v5.service import create_model_app
from .inference import GroundedAnalyzer, SYSTEM, retriever


def verify_runtime(root):
    root = Path(root)
    frozen = json.loads((root / "configs/frozen.json").read_text())
    for path, digest in frozen["files"].items():
        if sha(root / path) != digest:
            raise ValueError("Configuração da correção diverge do congelamento.")
    if __import__("hashlib").sha256(SYSTEM.encode()).hexdigest() != frozen["system_sha"]:
        raise ValueError("Instruções da correção divergentes.")


def create_grounded_app(root, baseline):
    root, baseline = Path(root).resolve(), Path(baseline).resolve()
    # Mantém verificação do pacote experimental anterior; não muda a seleção de pesos.
    if not (baseline / "configs/selected.json").exists():
        return create_model_app(baseline)
    verify_runtime(root)
    selected = json.loads((baseline / "configs/selected.json").read_text())
    adapter = baseline / selected["adapter_path"]
    if sha(adapter / "adapters.safetensors") != selected["adapter_sha"]:
        raise ValueError("Adaptador diverge da seleção original.")
    config = json.loads((baseline / "configs/model.json").read_text())

    def factory():
        generator = Generator(baseline / config["model_path"], adapter)
        if generator.metadata()["modelo"] != config["model"]:
            raise ValueError("Identidade do modelo diverge.")
        return GroundedAnalyzer(
            generator, retriever(read_jsonl(root / "base/chunks.jsonl")),
            threshold=json.loads((root / "configs/protocol.json").read_text())["threshold"],
        )

    return create_app(ThreadBoundAnalyzer(factory), demo_path=Path(__file__).parent.parent / "v5/demo.html")
