"""Consolida o subconjunto fixado antes da geração, preservando a revisão completa."""

import hashlib
import json
from pathlib import Path

from .analysis_sets import plan
from .review_metrics import FIELDS, metric_bounds, paired_intervals


def consolidate_clean(root):
    root = Path(root)
    p, plan_sha = plan(root)
    dest = root / "revisao/v3"
    full_path = dest / "reviewed_responses.jsonl"
    original = [json.loads(s) for s in full_path.read_text().splitlines()]
    excluded = set(p["excluded_case_ids"]["test"])
    rows = [r for r in original if r["case_id"] not in excluded]
    modes = sorted({r["mode"] for r in rows})
    if modes != ["final-A", "final-B", "final-C"]:
        raise ValueError("Três configurações completas são necessárias.")
    expected = p["confirmatory_counts"]["test"]
    if any(len([r for r in rows if r["mode"] == mode]) != expected for mode in modes):
        raise ValueError("Cobertura do subconjunto divergente.")
    fields = [*FIELDS, "integral_accuracy"]
    result = {
        "analysis_set": "without_identified_semantic_overlap",
        "plan_sha": plan_sha,
        "full_review_preserved": True,
        "full_review_sha": hashlib.sha256(full_path.read_bytes()).hexdigest(),
        "reviewer_kind": "ai_assisted_technical_review",
        "independent_human_review": False,
        "n_responses": len(rows),
        "n_excluded": len(original) - len(rows),
        "excluded_case_ids": sorted(excluded),
        "limitations": [
            "Anotações técnicas por IA, sujeitas a adjudicação humana independente.",
            "Intervalos condicionais aos rótulos técnicos e famílias sintéticas, não ao campo.",
            "Exclusões removem sobreposições identificadas; não certificam independência perfeita.",
        ],
        "modes": {
            mode: {
                "n": len(part),
                **{f: metric_bounds([r[f] for r in part]) for f in fields},
                "by_category": {
                    cat: {f: metric_bounds([r[f] for r in part if r["category"] == cat]) for f in fields}
                    for cat in sorted({r["category"] for r in part})
                },
            }
            for mode in modes
            if (part := [r for r in rows if r["mode"] == mode])
        },
        "comparisons": [
            paired_intervals(rows, a, b, f)
            for a, b in [("final-B", "final-A"), ("final-C", "final-A"), ("final-C", "final-B")]
            for f in ["semantic_correct", "integral_accuracy", "hallucination"]
        ],
    }
    with (dest / "clean_metrics.json").open("x") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return result
