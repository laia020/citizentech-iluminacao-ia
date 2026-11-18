"""Lê os adaptadores originais; sem fusão, quantização, novo treinamento ou sobrescrita."""

import hashlib
import json
import re
import zipfile
from pathlib import Path

import numpy as np
from safetensors.numpy import load


def load_adapter(root):
    root = Path(root)
    manifest = json.loads((root / "artefatos/runtime-manifest.json").read_text())
    config_root = root / "experimentos/v5-1.5b/configs"
    selected = json.loads((config_root / "selected.json").read_text())
    model = json.loads((config_root / "model.json").read_text())
    if (selected["adapter_sha"] != manifest["adapter_sha"]
            or any(model[k] != manifest[k] for k in ["model", "revision"])):
        raise ValueError("Pacote diverge do modelo ou adaptador selecionado.")
    archive = root / "artefatos" / manifest["archive"]
    if hashlib.sha256(archive.read_bytes()).hexdigest() != manifest["archive_sha"]:
        raise ValueError("Integridade do pacote inválida.")
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        if len(names) != len(set(names)) or set(names) != set(manifest["files"]):
            raise ValueError("Arquivos divergem do manifesto.")
        payload = {}
        for name in names:
            if Path(name).name != name:
                raise ValueError("Caminho inválido no ZIP.")
            payload[name] = z.read(name)
            if hashlib.sha256(payload[name]).hexdigest() != manifest["files"][name]:
                raise ValueError("SHA de arquivo inválido.")
    if hashlib.sha256(payload["adapters.safetensors"]).hexdigest() != selected["adapter_sha"]:
        raise ValueError("Adaptador não corresponde à seleção.")
    config = json.loads(payload["adapter_config.json"])
    params = config["lora_parameters"]
    if config["fine_tune_type"] != "lora" or params["rank"] <= 0 or not np.isfinite(params["scale"]):
        raise ValueError("Configuração LoRA não suportada.")
    weights = load(payload["adapters.safetensors"])
    pairs, layers = {}, set()
    for name, value in weights.items():
        match = re.fullmatch(r"model\.layers\.(\d+)\.(self_attn\.[qv]_proj)\.lora_([ab])", name)
        if not match or match[2] not in params["keys"]:
            raise ValueError("Tensor LoRA não esperado.")
        if value.dtype != np.float32 or value.ndim != 2 or not np.isfinite(value).all():
            raise ValueError("Tensor LoRA inválido.")
        prefix = name.rsplit(".", 1)[0]
        pairs.setdefault(prefix, {})[match[3]] = value
        layers.add(int(match[1]))
    if len(layers) != config["num_layers"] or len(pairs) != len(layers) * len(params["keys"]):
        raise ValueError("Camadas ou módulos incompletos.")
    for pair in pairs.values():
        if set(pair) != {"a", "b"} or pair["a"].shape[1] != params["rank"] or pair["b"].shape[0] != params["rank"]:
            raise ValueError("Par LoRA incompleto ou rank divergente.")
    return weights, config, manifest
