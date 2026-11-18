"""Publicação explícita de pacote verificado; aceita somente ZeroGPU, sem plano pago."""

import argparse
import hashlib
import json
from pathlib import Path

from huggingface_hub import HfApi, SpaceHardware


def publish(bundle, repo_id, expected_revision=None):
    bundle = Path(bundle).resolve()
    manifest = json.loads((bundle / "bundle-manifest.json").read_text())
    for name, expected in manifest.items():
        path = bundle / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("Pacote alterado após preparação; preparar novo pacote.")
    actual_files = {str(p.relative_to(bundle)) for p in bundle.rglob("*") if p.is_file()}
    if actual_files != set(manifest) | {"bundle-manifest.json"}:
        raise ValueError("Pacote contém arquivos não verificados.")
    api = HfApi()
    if repo_id.split("/")[0] != api.whoami()["name"]:
        raise ValueError("Destino não pertence à conta autenticada.")
    if api.repo_exists(repo_id, repo_type="space"):
        if expected_revision is None:
            raise FileExistsError("Space já existe; inspecionar antes de atualizar, sem substituição automática.")
        info = api.space_info(repo_id)
        runtime = api.get_space_runtime(repo_id)
        if info.sha != expected_revision or runtime.requested_hardware != SpaceHardware.ZERO_A10G:
            raise ValueError("Revisão ou hardware remoto divergente; nenhuma atualização realizada.")
    else:
        if expected_revision is not None:
            raise ValueError("Space da revisão esperada não existe.")
        api.create_repo(repo_id, repo_type="space", private=False, space_sdk="gradio",
                        space_hardware=SpaceHardware.ZERO_A10G, exist_ok=False)
    commit = api.upload_folder(repo_id=repo_id, repo_type="space", folder_path=bundle,
                               commit_message="Publica POC em nuvem com adaptador r1 verificado",
                               parent_commit=expected_revision)
    runtime = api.get_space_runtime(repo_id)
    return {"space": "https://huggingface.co/spaces/" + repo_id,
            "commit": commit.oid, "stage": runtime.stage,
            "hardware": runtime.hardware, "requested_hardware": runtime.requested_hardware,
            "paid_hardware_requested": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pacote", required=True)
    parser.add_argument("--space", required=True)
    parser.add_argument("--publicar", action="store_true")
    parser.add_argument("--atualizar-revisao", help="Revisão remota inspecionada; atualização recusa divergência.")
    args = parser.parse_args()
    if not args.publicar:
        parser.error("Nenhuma publicação realizada; --publicar precisa ser explícito.")
    print(json.dumps(publish(args.pacote, args.space, args.atualizar_revisao), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
