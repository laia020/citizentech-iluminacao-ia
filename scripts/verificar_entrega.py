"""Confere cobertura e procedência dos experimentos concluídos; não executa a LLM."""

import hashlib
import json
from pathlib import Path

from citizentech_ia.datasets import read_jsonl, sha, verify_freeze
from citizentech_ia.schemas import Occurrence

ROOT = Path(__file__).resolve().parents[1]


def main():
    verify_freeze(ROOT)
    progress = json.loads((ROOT / "runs/progress.json").read_text())
    if progress["state"] != "complete":
        raise ValueError("Experimentos ainda não concluídos.")
    gold = {r["case_id"]: r for r in read_jsonl(ROOT / "avaliacao/test.jsonl")}
    expected_ids = set(gold)
    report = {"frozen_artifacts_valid": True, "checks": {}, "scientific_review": "pending"}
    comparison = {}
    for name, mode in {
        "final-A": "base_sem_contexto",
        "final-B": "rag_simples",
        "final-C": "rag_finetuning",
    }.items():
        rows = read_jsonl(ROOT / "runs" / name / "responses.jsonl")
        metrics = json.loads((ROOT / "runs" / name / "metrics.json").read_text())
        if len(rows) != len(gold) or {r["case_id"] for r in rows} != expected_ids:
            raise ValueError(f"Cobertura incompleta/duplicada: {name}")
        if metrics["n"] != len(gold) or metrics["mode"] != mode or metrics["split"] != "test":
            raise ValueError(f"Métricas de outro experimento: {name}")
        if metrics["test_sha"] != sha(ROOT / "avaliacao/test.jsonl"):
            raise ValueError(f"Teste diferente: {name}")
        if sha(ROOT / "runs" / name / "responses.jsonl") != sha(
            ROOT / "avaliacao/respostas" / f"{name}.jsonl"
        ):
            raise ValueError(f"Cópia de respostas divergente: {name}")
        for row in rows:
            if "messages" not in row:
                raise ValueError(f"Caso sem prompt auditável: {row['case_id']}")
            user = json.loads(row["messages"][1]["content"])
            occurrence = Occurrence.model_validate(gold[row["case_id"]]["input"])
            if user["OCORRENCIA"] != occurrence.model_dump(mode="json", exclude={"ocorrencia_id"}):
                raise ValueError(f"Prompt divergente ou metadados indevidos: {row['case_id']}")
            if set(user) != {"OCORRENCIA", "CONTEXTO"}:
                raise ValueError("Campos adicionais no prompt.")
            if mode == "base_sem_contexto" and user["CONTEXTO"]:
                raise ValueError("Baseline recebeu documentos.")
        comparison[name] = {r["case_id"]: r for r in rows}
        report["checks"][name] = {
            "cases": len(rows),
            "prompts_without_identifiers": True,
            "responses_sha": sha(ROOT / "runs" / name / "responses.jsonl"),
            "structural_failures": sum(not r["valid_json_and_refs"] for r in rows),
            "status_mismatches": sum(not r["status_match"] for r in rows),
        }
    for case_id in expected_ids:
        if comparison["final-B"][case_id]["chunks"] != comparison["final-C"][case_id]["chunks"]:
            raise ValueError(f"Contextos B/C diferentes: {case_id}")
    selected_sha = sha(ROOT / "adapters/selected/best/adapters.safetensors")
    final_metrics = json.loads((ROOT / "runs/final-C/metrics.json").read_text())
    if final_metrics["model"]["adaptador"] != selected_sha:
        raise ValueError("Adaptador final não corresponde ao avaliado.")
    report["selected_adapter_sha"] = selected_sha
    report["retrieved_contexts_equal_B_C"] = True
    base = ROOT / "models/qwen-7b-4bit"
    provenance = json.loads((base / "provenance.json").read_text())
    report["base_weight_sha"] = {}
    for filename, expected in provenance["files"].items():
        with (base / filename).open("rb") as f:
            actual = hashlib.file_digest(f, "sha256").hexdigest()
        if actual != expected:
            raise ValueError(f"Peso base alterado: {filename}")
        report["base_weight_sha"][filename] = actual
    report["source_sha"] = {
        str(p.relative_to(ROOT)): sha(p)
        for p in sorted(
            [*ROOT.glob("src/**/*.py"), *ROOT.glob("scripts/*.py"), ROOT / "pyproject.toml", ROOT / "uv.lock"]
        )
    }
    report["limitations"] = [
        "Revisão semântica humana independente pendente.",
        "Dados sintéticos; não demonstram desempenho em campo.",
        "Integração real do grupo e publicação pendentes.",
    ]
    # Small scientific records are reviewable without distributing weights or local environments.
    for name in ["smoke-01", "lr1e5", "lr5e5"]:
        dest = ROOT / "avaliacao/treinamento" / name
        dest.mkdir(parents=True, exist_ok=False)
        for filename in ["summary.json", "provenance.json", "metrics.jsonl"]:
            source = ROOT / "adapters" / name / filename
            with (dest / filename).open("xb") as f:
                f.write(source.read_bytes())
    with (ROOT / "docs/validacao-entrega.json").open("x") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
