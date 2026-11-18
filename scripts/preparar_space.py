"""Prepara um pacote novo e verificável para Space; nunca publica implicitamente."""

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from citizentech_ia.cloud.weights import load_adapter
from citizentech_ia.datasets import verify_freeze
from citizentech_ia.v5.inference import SYSTEM


def build_bundle(root, destination):
    root, destination = Path(root).resolve(), Path(destination).resolve()
    load_adapter(root)
    verify_freeze(root / "experimentos/v5-1.5b", system_prompt=SYSTEM)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError("Destino existente; escolha outro nome, sem sobrescrever.")
    source = root / "deploy/hf-space"
    required = [source / name for name in ["app.py", "SPACE_README.md", "requirements.txt"]]
    if not all(p.is_file() for p in required):
        raise FileNotFoundError("Preparação incompleta; faltam inicializador, README ou dependências exportadas.")
    destination.mkdir(parents=True)
    shutil.copy2(required[0], destination / "app.py")
    shutil.copy2(required[1], destination / "README.md")
    shutil.copy2(required[2], destination / "requirements.txt")
    shutil.copytree(root / "src", destination / "src", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copytree(root / "artefatos", destination / "artefatos")
    experiment = destination / "experimentos/v5-1.5b"
    experiment.mkdir(parents=True)
    for name in ["configs", "base", "dados"]:
        shutil.copytree(root / "experimentos/v5-1.5b" / name, experiment / name)
    (experiment / "avaliacao").mkdir()
    shutil.copy2(root / "experimentos/v5-1.5b/avaliacao/test.jsonl", experiment / "avaliacao/test.jsonl")
    page = (root / "src/citizentech_ia/v5/demo.html").read_text()
    page = page.replace("serviço local", "serviço em nuvem").replace("modelo local", "modelo em nuvem")
    page = page.replace("IA local", "IA em nuvem").replace("API local", "API em nuvem")
    page = page.replace("Modelo local", "Modelo em nuvem").replace("tela local", "tela de demonstração")
    page = page.replace("Somente neste Mac", "Execução na nuvem")
    (destination / "cloud-demo.html").write_text(page)
    hashes = {}
    for p in sorted(destination.rglob("*")):
        if p.is_file():
            with p.open("rb") as stream:
                hashes[str(p.relative_to(destination))] = hashlib.file_digest(stream, "sha256").hexdigest()
    (destination / "bundle-manifest.json").write_text(json.dumps(hashes, indent=2))
    return {"path": str(destination), "files": len(hashes), "sha256": hashes,
            "adapter_sha": load_adapter(destination)[2]["adapter_sha"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", required=True)
    args = parser.parse_args()
    result = build_bundle(Path(__file__).resolve().parents[1], args.destino)
    print(json.dumps({k: v for k, v in result.items() if k != "sha256"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
