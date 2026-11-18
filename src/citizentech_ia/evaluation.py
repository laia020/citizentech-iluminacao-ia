"""Resultados automáticos não substituem revisão humana de fundamentação."""

import csv
import json
import shutil
import time
from pathlib import Path

import numpy as np

from .datasets import read_jsonl, sha, verify_freeze
from .inference import Analyzer, ContextOverflow, InvalidGeneration, MLXGenerator, strict_json
from .pipeline import load_retriever
from .retrieval import retrieval_metrics
from .schemas import Analysis, Occurrence


def grade_structure(analyzer, raw, chunks, occurrence, expected_status):
    """Status requires a schema-valid response; bad references are scored separately."""
    result = {
        "json_syntax_valid": False,
        "schema_valid": False,
        "valid_json_and_refs": False,
        "status_match": False,
    }
    try:
        decoded = strict_json(raw)
        result["json_syntax_valid"] = True
        analysis = Analysis.model_validate(decoded)
        result["schema_valid"] = True
        result["analysis"] = analysis.model_dump()
        result["status_match"] = analysis.status == expected_status
        analyzer.parse(raw, chunks, occurrence)
        result["valid_json_and_refs"] = True
    except (ValueError, InvalidGeneration):
        result["error"] = "invalid_generation"
    return result


def evaluate_run(root, name, mode, adapter=None, split="test", limit=None):
    import mlx.core as mx

    root = Path(root).resolve()
    verify_freeze(root)
    output = root / "runs" / name
    output.mkdir(exist_ok=False)
    rows = read_jsonl(root / ("avaliacao/test.jsonl" if split == "test" else "dados/valid.jsonl"))
    if limit:
        rows = rows[:limit]
    generator = MLXGenerator(root / "models/qwen-7b-4bit", adapter, require_adapter=mode == "rag_finetuning")
    retrieval_config = json.loads((root / "configs/retrieval.json").read_text())
    a = Analyzer(generator, load_retriever(root), threshold=retrieval_config["threshold"], mode=mode)
    results = []
    # Warm-up is excluded from measured cases and never includes test input.
    generator.generate([{"role": "user", "content": "Responda apenas OK."}], max_tokens=4)
    with (output / "responses.jsonl").open("x") as f:
        for i, row in enumerate(rows):
            occurrence = Occurrence.model_validate(row["input"])
            start = time.perf_counter()
            result = {
                "case_id": row["case_id"],
                "category": row["category"],
                "split": split,
                "mode": mode,
                "expected_status": row["target"]["status"],
                "review_status": "pendente_revisao_humana",
            }
            try:
                messages, chunks, n_tokens = a.prepare(occurrence)
                raw = generator.generate(messages, max_tokens=a.max_output)
                result.update(
                    {
                        "raw": raw,
                        "messages": messages,
                        "chunks": chunks,
                        "input_tokens": n_tokens,
                        "output_tokens": generator.count_tokens(raw),
                    }
                )
                result.update(grade_structure(a, raw, chunks, occurrence, row["target"]["status"]))
                result["retrieval"] = retrieval_metrics(
                    [c["chunk_id"] for c in chunks], row["relevant_chunks"]
                )
            except ContextOverflow:
                result.update(
                    {
                        "json_syntax_valid": False,
                        "schema_valid": False,
                        "valid_json_and_refs": False,
                        "status_match": False,
                        "error": "context_overflow",
                    }
                )
            result["elapsed_s"] = time.perf_counter() - start
            result["peak_memory_gb"] = mx.get_peak_memory() / 1e9
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
            f.flush()
            results.append(result)
            print(
                json.dumps(
                    {
                        "run": name,
                        "case": i + 1,
                        "total": len(rows),
                        "valid": result["valid_json_and_refs"],
                        "status_match": result["status_match"],
                        "seconds": round(result["elapsed_s"], 1),
                    }
                ),
                flush=True,
            )
    metrics = {
        "mode": mode,
        "split": split,
        "n": len(results),
        "json_syntax_valid_rate": float(np.mean([r["json_syntax_valid"] for r in results])),
        "schema_valid_rate": float(np.mean([r["schema_valid"] for r in results])),
        "valid_json_and_refs_rate": np.mean([r["valid_json_and_refs"] for r in results]).item(),
        "status_match_rate": np.mean([r["status_match"] for r in results]).item(),
        "median_seconds": float(np.median([r["elapsed_s"] for r in results])),
        "p95_seconds": float(np.percentile([r["elapsed_s"] for r in results], 95)),
        "peak_memory_gb": mx.get_peak_memory() / 1e9,
        "semantic_correctness": "PENDENTE: status_match não é acerto semântico ou fundamentação.",
        "model": generator.metadata(),
        "base_sha": sha(root / "base/chunks.jsonl"),
        "test_sha": sha(root / ("avaliacao/test.jsonl" if split == "test" else "dados/valid.jsonl")),
        "retrieval_config_sha": sha(root / "configs/retrieval.json"),
        "by_category": {
            c: {
                "n": sum(r["category"] == c for r in results),
                "status_match_rate": float(
                    np.mean([r["status_match"] for r in results if r["category"] == c])
                ),
            }
            for c in {r["category"] for r in results}
        },
    }
    metrics["retrieval_respondible"] = {
        key: float(
            np.mean(
                [r.get("retrieval", {}).get(key, 0) or 0 for r in results if r["category"] == "respondivel"]
            )
        )
        for key in ["recall@1", "recall@3"]
    }
    (output / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2))
    with (output / "revisao_humana.csv").open("x") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "case_id",
                "correto",
                "fundamentado",
                "alucinacao",
                "recusa_adequada",
                "justificativa",
                "revisor",
            ],
        )
        writer.writeheader()
        writer.writerows({"case_id": r["case_id"]} for r in results)
    return metrics


def publish_comparison(root, run_names):
    root = Path(root)
    metrics = [json.loads((root / "runs" / n / "metrics.json").read_text()) for n in run_names]
    (root / "avaliacao/placar.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2))
    destination = root / "avaliacao/respostas"
    destination.mkdir(exist_ok=True)
    for name in run_names:
        shutil.copy2(root / "runs" / name / "responses.jsonl", destination / f"{name}.jsonl")
    errors, used = [], set()
    gold = {row["case_id"]: row for row in read_jsonl(root / "avaliacao/test.jsonl")}
    pools = {name: read_jsonl(root / "runs" / name / "responses.jsonl") for name in run_names}
    while len(errors) < 5:
        before = len(errors)
        for name in run_names:
            for row in pools[name]:
                family = row["case_id"].rsplit("-v", 1)[0]
                key = (row["category"], family)
                if key in used or (row["status_match"] and row["valid_json_and_refs"]):
                    continue
                used.add(key)
                error = row.get("error", "status_mismatch")
                if error == "invalid_generation":
                    cause = (
                        "Saída não atende ao esquema ou cita fonte fora do contexto; revisar resposta bruta."
                    )
                    correction = "Revisar exemplos de formato e casos de contexto ausente em uma nova versão; manter o teste original congelado."
                else:
                    cause = f"Status gerado diverge do gabarito na categoria {row['category']}; pode haver ambiguidade ou generalização inadequada."
                    correction = "Revisar evidências e gabarito; ampliar cenários da categoria somente em novo ciclo de treino/validação e medir em avaliação separada."
                errors.append(
                    {
                        "case_id": row["case_id"],
                        "run_id": name,
                        "mode": row["mode"],
                        "raw": row.get("raw"),
                        "expected_status": row["expected_status"],
                        "input": gold[row["case_id"]]["input"],
                        "expected_analysis": gold[row["case_id"]]["target"],
                        "retrieved_chunks": row.get("chunks", []),
                        "observed_status": row.get("analysis", {}).get("status"),
                        "error": error,
                        "cause_hypothesis": cause,
                        "proposed_correction": correction,
                    }
                )
                break
            if len(errors) >= 5:
                break
        if len(errors) == before:
            break
    (root / "avaliacao/cinco_erros.json").write_text(json.dumps(errors, ensure_ascii=False, indent=2))
    return metrics


def aggregate_review(root, run_name):
    """Só calcula julgamento semântico se o CSV estiver totalmente preenchido."""
    root = Path(root)
    directory = root / "runs" / run_name
    records = read_jsonl(directory / "responses.jsonl")
    if not records:
        raise ValueError("Nenhum caso para revisar.")
    with (directory / "revisao_humana.csv").open(newline="") as f:
        review = list(csv.DictReader(f))
    if len(review) != len(records) or {r["case_id"] for r in review} != {r["case_id"] for r in records}:
        raise ValueError("Casos da revisão diferem das respostas.")
    if len({r["case_id"] for r in review}) != len(review):
        raise ValueError("Caso duplicado na revisão.")
    for row in review:
        if not row["revisor"].strip() or not row["justificativa"].strip():
            raise ValueError("Revisão incompleta: identifique revisor e justificativa por caso.")
        if any(
            row[k] not in ("0", "1") for k in ["correto", "fundamentado", "alucinacao", "recusa_adequada"]
        ):
            raise ValueError("Revisão incompleta: use 0/1 sem preencher por padrão.")
    metrics = {
        k: sum(int(r[k]) for r in review) / len(review)
        for k in ["correto", "fundamentado", "alucinacao", "recusa_adequada"]
    }
    metrics["n"] = len(review)
    metrics["review_sha"] = sha(directory / "revisao_humana.csv")
    (directory / "human_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2))
    return metrics
