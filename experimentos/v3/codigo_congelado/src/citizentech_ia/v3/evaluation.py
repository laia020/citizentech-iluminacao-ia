"""Experimento v3: mesmas condições para A/B/C; julgamentos semânticos ficam separados."""

import csv
import json
import time
from pathlib import Path

import numpy as np

from ..datasets import read_jsonl, sha, verify_freeze
from ..evaluation import grade_structure
from ..inference import MLXGenerator, strict_json
from ..retrieval import retrieval_metrics
from ..schemas import Occurrence
from .inference import SYSTEM, ReviewedAnalyzer
from .pipeline import retriever


def evaluate(root, name, mode, adapter=None, split="valid"):
    import mlx.core as mx
    import psutil

    root = Path(root).resolve()
    verify_freeze(root, system_prompt=SYSTEM)
    if split == "test" and not (root / "configs/selected.json").exists():
        raise ValueError("Teste só é aberto após seleção e registro na validação.")
    dest = root / "runs" / name
    dest.mkdir(exist_ok=False)
    rows = read_jsonl(root / ("avaliacao/test.jsonl" if split == "test" else "dados/valid.jsonl"))
    generator = MLXGenerator(root / "models/qwen-7b-4bit", adapter, require_adapter=mode == "rag_finetuning")
    threshold = json.loads((root / "configs/retrieval.json").read_text())["threshold"]
    a = ReviewedAnalyzer(generator, retriever(root), threshold=threshold, mode=mode)
    generator.generate([{"role": "user", "content": "Responda apenas OK."}], max_tokens=4)
    results = []
    swap_start = psutil.swap_memory().used
    with (dest / "responses.jsonl").open("x") as f:
        for i, row in enumerate(rows):
            inp = Occurrence.model_validate(row["input"])
            messages, chunks, tokens = a.prepare(inp)
            start = time.perf_counter()
            raw = generator.generate(messages, max_tokens=a.max_output)
            duration = time.perf_counter() - start
            structure = grade_structure(a, raw, chunks, inp, row["target"]["status"])
            status_only = False
            try:
                decoded = strict_json(raw)
                status_only = isinstance(decoded, dict) and decoded.get("status") == row["target"]["status"]
            except ValueError:
                pass
            result = {
                "case_id": row["case_id"],
                "family": row["scenario_family"],
                "category": row["category"],
                "split": split,
                "mode": mode,
                "raw": raw,
                "messages": messages,
                "chunks": chunks,
                **structure,
                "status_only_match": status_only,
                "elapsed_s": duration,
                "input_tokens": tokens,
                "output_tokens": generator.count_tokens(raw),
                "peak_memory_gb": mx.get_peak_memory() / 1e9,
                "available_gb": psutil.virtual_memory().available / 1e9,
                "swap_growth_gb": (psutil.swap_memory().used - swap_start) / 1e9,
                "retrieval": retrieval_metrics([c["chunk_id"] for c in chunks], row["relevant_chunks"]),
                "semantic_judgment": "pending_technical_review_not_human",
            }
            results.append(result)
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
            f.flush()
            print(
                json.dumps(
                    {
                        "run": name,
                        "case": i + 1,
                        "total": len(rows),
                        "schema": structure["schema_valid"],
                        "status_only": status_only,
                        "seconds": round(duration, 2),
                    }
                ),
                flush=True,
            )
    metrics = {
        "version": "v3",
        "mode": mode,
        "split": split,
        "n": len(results),
        **{
            key + "_rate": float(np.mean([r[key] for r in results]))
            for key in [
                "json_syntax_valid",
                "schema_valid",
                "valid_json_and_refs",
                "status_only_match",
                "status_match",
            ]
        },
        "median_seconds": float(np.median([r["elapsed_s"] for r in results])),
        "p95_seconds": float(np.percentile([r["elapsed_s"] for r in results], 95)),
        "peak_memory_gb": mx.get_peak_memory() / 1e9,
        "model": generator.metadata(),
        "frozen_manifest_sha": sha(root / "configs/frozen_manifest.json"),
        "test_file_sha": sha(root / ("avaliacao/test.jsonl" if split == "test" else "dados/valid.jsonl")),
        "semantic_accuracy": "pending; structure/status do not establish factual correctness",
        "hallucination_rate": "pending; never inferred solely from JSON or status",
        "by_category": {
            c: {
                "n": sum(r["category"] == c for r in results),
                "status_only_match_rate": float(
                    np.mean([r["status_only_match"] for r in results if r["category"] == c])
                ),
                "schema_rate": float(np.mean([r["schema_valid"] for r in results if r["category"] == c])),
            }
            for c in sorted({r["category"] for r in results})
        },
        "retrieval_all": {
            key: float(np.mean([r["retrieval"][key] for r in results if r["retrieval"][key] is not None]))
            for key in ["recall@1", "recall@3"]
        },
        "retrieval_respondible": {
            key: float(
                np.mean(
                    [
                        r["retrieval"][key]
                        for r in results
                        if r["category"] == "respondivel" and r["retrieval"][key] is not None
                    ]
                )
            )
            for key in ["recall@1", "recall@3"]
        },
    }
    (dest / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2))
    with (dest / "revisao-tecnica.csv").open("x") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "case_id",
                "semantic_correct",
                "hallucination",
                "grounded",
                "refusal_adequate",
                "reason",
                "reviewer_kind",
            ],
        )
        w.writeheader()
        w.writerows({"case_id": r["case_id"]} for r in results)
    return metrics
