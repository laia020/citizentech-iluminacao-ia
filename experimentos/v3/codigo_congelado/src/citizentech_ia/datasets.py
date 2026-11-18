import hashlib
import json
from collections import defaultdict
from pathlib import Path

from .retrieval import normalize
from .schemas import Analysis, Occurrence


def read_jsonl(path):
    result = []
    for line_no, line in enumerate(Path(path).read_text().splitlines(), 1):
        if line.strip():
            try:
                result.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"JSONL inválido: {path}:{line_no}") from e
    return result


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_splits(rows):
    ids, families, inputs = set(), {}, {}
    counts = defaultdict(int)
    for row in rows:
        cid, split, family = row["case_id"], row["split"], row["scenario_family"]
        if split not in {"train", "valid", "test", "exploratory"}:
            raise ValueError("Split desconhecido.")
        if cid in ids:
            raise ValueError("case_id duplicado.")
        ids.add(cid)
        if family in families and families[family] != split:
            raise ValueError("Família em múltiplos splits.")
        families[family] = split
        inp = Occurrence.model_validate(row["input"])
        identity = normalize(
            json.dumps(
                inp.model_dump(mode="json", exclude={"ocorrencia_id"}), sort_keys=True, ensure_ascii=False
            )
        )
        if identity in inputs:
            raise ValueError("Entrada duplicada.")
        inputs[identity] = split
        if "target" in row:
            Analysis.model_validate(row["target"])
        counts[split] += 1
    return dict(counts)


def verify_freeze(root, system_prompt=None):
    from .inference import SYSTEM

    root = Path(root)
    manifest = json.loads((root / "configs/frozen_manifest.json").read_text())
    if hashlib.sha256((SYSTEM if system_prompt is None else system_prompt).encode()).hexdigest() != manifest["system_sha"]:
        raise ValueError("Prompt congelado alterado. Crie uma nova versão de experimento.")
    for relative, expected in manifest["artifacts"].items():
        if sha(root / relative) != expected:
            raise ValueError(f"Artefato congelado alterado: {relative}. Crie uma nova versão de experimento.")
    dataset_manifest = json.loads((root / "dados/manifest.json").read_text())
    for relative, expected in dataset_manifest["hashes"].items():
        if sha(root / relative) != expected:
            raise ValueError(f"Artefato original alterado: {relative}. Crie uma nova versão de experimento.")
    return True
