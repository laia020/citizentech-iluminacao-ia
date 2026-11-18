"""Preparação explícita de reprodução; check não baixa, converte, treina ou altera arquivos."""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def digest(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def manifest(root):
    return json.loads((Path(root) / "artefatos/runtime-manifest.json").read_text())


def import_adapter(root, destination):
    root, destination = Path(root), Path(destination)
    m = manifest(root)
    bundle = root / "artefatos" / m["archive"]
    if digest(bundle) != m["archive_sha"]:
        raise ValueError("Falha de integridade no pacote do adaptador.")
    if destination.exists():
        valid = all((destination / name).is_file() and digest(destination / name) == m["files"][name]
                    for name in ["adapter_config.json", "adapters.safetensors"])
        if not valid:
            raise ValueError("Adaptador existente diverge; nenhum arquivo foi sobrescrito.")
        return {"adapter": "existing_identical", "path": str(destination)}
    if destination.is_symlink():
        raise ValueError("Destino existente é um vínculo; inspecione antes de continuar.")
    with zipfile.ZipFile(bundle) as z:
        names = z.namelist()
        if len(names) != len(set(names)) or set(names) != set(m["files"]):
            raise ValueError("Conteúdo do pacote diverge do manifesto de integridade.")
        payload = {}
        for name in names:
            if Path(name).name != name:
                raise ValueError("Caminho inválido no pacote.")
            data = z.read(name)
            if hashlib.sha256(data).hexdigest() != m["files"][name]:
                raise ValueError("Falha de integridade em arquivo do pacote.")
            payload[name] = data
    if hashlib.sha256(payload["adapters.safetensors"]).hexdigest() != m["adapter_sha"]:
        raise ValueError("Pesos divergem da seleção registrada.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent, prefix=".adapter-import-") as temp:
        stage = Path(temp) / "verified"
        stage.mkdir()
        for name in ["adapter_config.json", "adapters.safetensors"]:
            (stage / name).write_bytes(payload[name])
        # Refuse collisions even if another process created the target during verification.
        destination.mkdir(exist_ok=False)
        for p in stage.iterdir():
            shutil.copy2(p, destination / p.name)
    return {"adapter": "imported_verified", "path": str(destination)}


def ensure_model_link(root):
    root = Path(root).resolve()
    models = root / "models"
    models.mkdir(exist_ok=True)
    link = root / "experimentos/v5-1.5b/models"
    if link.exists() or link.is_symlink():
        if link.resolve() != models.resolve():
            raise ValueError("Vínculo models existente aponta para outro local; inspecione, sem sobrescrita.")
    else:
        link.symlink_to("../../models", target_is_directory=True)


def prepare_base(root, download=False, convert=False):
    root = Path(root).resolve()
    m = manifest(root)
    original, converted = root / "models/qwen-1.5b-original", root / "models/qwen-1.5b-fp16"
    source = {"model": m["model"], "revision": m["revision"]}
    marker = original / ".download_source.json"
    if download:
        if original.exists() and any(original.iterdir()) and (
            not marker.exists() or any(json.loads(marker.read_text()).get(k) != v for k, v in source.items())
        ):
            raise ValueError("Base original existente sem procedência correspondente; não sobrescrita.")
        original.mkdir(parents=True, exist_ok=True)
        if not marker.exists():
            marker.write_text(json.dumps(source, indent=2))
        from huggingface_hub import snapshot_download

        snapshot_download(m["model"], revision=m["revision"], local_dir=original, token=False,
                          allow_patterns=["*.safetensors", "*.json", "*.txt", "*.model", "LICENSE", "README.md"])
    if convert:
        if converted.exists():
            p = converted / "provenance.json"
            if not p.exists() or any(json.loads(p.read_text()).get(k) != v for k, v in source.items()):
                raise ValueError("Base convertida existente sem procedência correspondente; não sobrescrita.")
        else:
            if not marker.is_file() or any(json.loads(marker.read_text()).get(k) != v for k, v in source.items()):
                raise ValueError("Obtenha primeiro a revisão original oficial indicada no manifesto.")
            subprocess.run([sys.executable, "-m", "mlx_lm", "convert", "--hf-path", str(original),
                            "--mlx-path", str(converted), "--dtype", "float16"], check=True)
            weight_hashes = {p.name: digest(p) for p in converted.glob("*.safetensors")}
            if not weight_hashes:
                raise ValueError("Conversão não produziu pesos; inspecione o destino preservado.")
            (converted / "provenance.json").write_text(json.dumps({
                **source, "license": m["base_license"], "files": weight_hashes,
                "conversion": "mlx_lm convert --dtype float16; no quantization",
            }, indent=2))
        p = json.loads((converted / "provenance.json").read_text())
        if any(digest(converted / name) != expected for name, expected in p["files"].items()):
            raise ValueError("Pesos existentes divergem da procedência; não sobrescritos.")
    ensure_model_link(root)


def check(root):
    root = Path(root).resolve()
    m = manifest(root)
    experiment = root / "experimentos/v5-1.5b"
    selection = json.loads((experiment / "configs/selected.json").read_text())
    adapter = experiment / selection["adapter_path"] / "adapters.safetensors"
    base = root / "models/qwen-1.5b-fp16/model.safetensors"
    actual = digest(base) if base.exists() else None
    return {
        "python": sys.version.split()[0], "model": m["model"], "revision": m["revision"],
        "archive_verified": digest(root / "artefatos" / m["archive"]) == m["archive_sha"],
        "base_present": base.exists(), "base_sha_matches_original": actual == m["base_fp16_canonical_sha"],
        "model_link_correct": (experiment / "models").resolve() == (root / "models").resolve(),
        "adapter_present_and_verified": adapter.exists() and digest(adapter) == selection["adapter_sha"],
        "check_did_not_execute_model_or_training": True,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["check", "import-adapter", "base"])
    parser.add_argument("--download", action="store_true", help="Usa rede/disco explicitamente.")
    parser.add_argument("--convert", action="store_true", help="Converte a base local; usa memória/GPU/disco.")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.command == "check":
        print(json.dumps(check(root), ensure_ascii=False, indent=2))
    elif args.command == "import-adapter":
        selection = json.loads((root / "experimentos/v5-1.5b/configs/selected.json").read_text())
        print(json.dumps(import_adapter(root, root / "experimentos/v5-1.5b" / selection["adapter_path"])))
        ensure_model_link(root)
    else:
        if not (args.download or args.convert):
            parser.error("Escolha --download e/ou --convert; nenhuma operação pesada é implícita.")
        prepare_base(root, download=args.download, convert=args.convert)


if __name__ == "__main__":
    main()
