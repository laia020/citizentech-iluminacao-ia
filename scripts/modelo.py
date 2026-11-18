"""Obtenção e conversão explícitas do modelo público fixado; sem upload."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description="baixar usa rede/disco; converter usa GPU/disco. Não treina.")
parser.add_argument("etapa", choices=["baixar", "converter"])
a = parser.parse_args()
config = json.loads((ROOT / "configs/model.json").read_text())
if config["model"] != "Qwen/Qwen2.5-7B-Instruct":
    raise SystemExit("Modelo fora da especificação.")
original = ROOT / "models/original"
marker = original / ".download_source.json"
if a.etapa == "baixar":
    if original.exists() and any(original.iterdir()) and not marker.exists():
        raise SystemExit(
            "Pasta original já contém dados sem marcador de origem. Inspecione; não sobrescrita."
        )
    source = {"model": config["model"], "revision": config["revision"]}
    if marker.exists() and json.loads(marker.read_text()) != source:
        raise SystemExit("Revisão existente difere da configurada. Preserve a pasta e use nova versão.")
    original.mkdir(parents=True, exist_ok=True)
    marker.write_text(json.dumps(source, indent=2))
    from huggingface_hub import snapshot_download

    snapshot_download(
        config["model"],
        revision=config["revision"],
        local_dir=original,
        allow_patterns=["*.safetensors", "*.json", "*.txt", "*.model", "LICENSE", "README.md"],
        max_workers=3,
    )
else:
    target = ROOT / "models/qwen-7b-4bit"
    if target.exists():
        raise SystemExit("Destino convertido já existe; não sobrescrito.")
    if not (original / "config.json").is_file():
        raise SystemExit("Modelo original local não encontrado.")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "mlx_lm",
            "convert",
            "--hf-path",
            str(original),
            "--mlx-path",
            str(target),
            "-q",
            "--q-bits",
            "4",
            "--q-group-size",
            "64",
            "--dtype",
            "float16",
        ],
        check=True,
    )
    from citizentech_ia.datasets import sha

    provenance = {**config, "files": {p.name: sha(p) for p in target.glob("*.safetensors")}}
    (target / "provenance.json").write_text(json.dumps(provenance, indent=2))
print("Etapa concluída:", a.etapa)
