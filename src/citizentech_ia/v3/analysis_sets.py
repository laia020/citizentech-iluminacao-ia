"""Subconjuntos de análise fixados antes da geração, sem alterar saídas do modelo."""

import hashlib
import json
from pathlib import Path

import numpy as np


def plan(root):
    root = Path(root)
    path = root / "configs/clean_holdout_plan.json"
    expected = json.loads((root / "configs/clean_holdout_freeze.json").read_text())["plan_sha"]
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise ValueError("Plano de análise alterado depois do congelamento.")
    result = json.loads(path.read_text())
    for relative, digest in result["source_hashes"].items():
        if hashlib.sha256((root / relative).read_bytes()).hexdigest() != digest:
            raise ValueError("Dados usados no plano de análise foram alterados.")
    return result, actual


def summarize(root, run):
    root = Path(root)
    p, digest = plan(root)
    directory = root / "runs" / run
    full = json.loads((directory / "metrics.json").read_text())
    rows = [json.loads(s) for s in (directory / "responses.jsonl").read_text().splitlines()]
    excluded = set(p["excluded_case_ids"][full["split"]])
    selected = [r for r in rows if r["case_id"] not in excluded]
    if len(selected) != p["confirmatory_counts"][full["split"]]:
        raise ValueError("Cobertura do subconjunto divergente.")
    fields = ["json_syntax_valid", "schema_valid", "valid_json_and_refs", "status_only_match", "status_match"]
    result = {
        "analysis_set": "without_identified_semantic_overlap",
        "plan_sha": digest,
        "mode": full["mode"],
        "split": full["split"],
        "n": len(selected),
        "n_full": len(rows),
        "n_excluded": len(rows) - len(selected),
        **{f + "_rate": float(np.mean([r[f] for r in selected])) for f in fields},
        "median_seconds": float(np.median([r["elapsed_s"] for r in selected])),
        "p95_seconds": float(np.percentile([r["elapsed_s"] for r in selected], 95)),
        "model": full["model"],
        "retrieval_respondible": {
            k: float(np.mean([r["retrieval"][k] for r in selected if r["category"] == "respondivel"]))
            for k in ["recall@1", "recall@3"]
        },
        "retained_case_ids": [r["case_id"] for r in selected],
        "excluded_case_ids": sorted(excluded),
        "full_metrics_preserved": True,
    }
    with (directory / "clean_metrics.json").open("x") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return result
