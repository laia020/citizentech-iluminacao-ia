"""Consolidação transparente da revisão técnica, incluindo julgamentos incertos."""

import csv
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

import numpy as np

FIELDS = ["semantic_correct", "hallucination", "grounded", "refusal_adequate"]


def metric_bounds(values):
    n = len(values)
    if not n:
        raise ValueError("Métrica sem casos.")
    positives = sum(v == 1 for v in values)
    unknown = sum(v is None for v in values)
    return {
        "n": n,
        "positive": positives,
        "negative": n - positives - unknown,
        "uncertain": unknown,
        "lower_rate": positives / n,
        "upper_rate": (positives + unknown) / n,
    }


def integral_score(structural, decision):
    values = [
        structural["schema_valid"],
        structural["valid_json_and_refs"],
        decision["semantic_correct"],
        decision["grounded"],
        decision["refusal_adequate"],
        None if decision["hallucination"] is None else 1 - decision["hallucination"],
    ]
    if any(v == 0 for v in values):
        return 0
    return None if any(v is None for v in values) else 1


def numeric_flags(member, group, source_chunks):
    # A screening aid only: quoting a number from an injected request is not a new factual claim.
    available = (
        json.dumps(member["input"], ensure_ascii=False)
        + " "
        + " ".join(source_chunks[c] for c in group["context_ids"])
    )
    try:
        data = json.loads(group["raw"])
        candidate = json.dumps(
            {k: v for k, v in data.items() if k not in ["fontes", "status"]}, ensure_ascii=False
        )
    except (ValueError, AttributeError):
        candidate = group["raw"]
    pattern = r"(?<!\w)\d+(?:[.,]\d+)?"
    return sorted(set(re.findall(pattern, candidate)) - set(re.findall(pattern, available)))


def paired_intervals(rows, candidate, reference, field, seed=42, replicates=5000):
    modes = {mode: {r["case_id"]: r for r in rows if r["mode"] == mode} for mode in [candidate, reference]}
    if set(modes[candidate]) != set(modes[reference]):
        raise ValueError("Comparação deve usar exatamente os mesmos casos.")
    strata = defaultdict(lambda: defaultdict(list))
    for cid, row in modes[candidate].items():
        strata[row["category"]][row["family"]].append(cid)
    arrays = {}
    for cid in modes[candidate]:
        a, b = modes[candidate][cid][field], modes[reference][cid][field]
        al, ah = (0, 1) if a is None else (a, a)
        bl, bh = (0, 1) if b is None else (b, b)
        # Positive favors candidate: more correct or fewer hallucinations.
        arrays[cid] = (bl - ah, bh - al) if field == "hallucination" else (al - bh, ah - bl)
    low = float(np.mean([x[0] for x in arrays.values()]))
    high = float(np.mean([x[1] for x in arrays.values()]))
    rng = np.random.default_rng(seed)
    bootstrap = []
    strata_values = [list(families.values()) for families in strata.values()]
    for _ in range(replicates):
        ids = []
        for families in strata_values:
            for j in rng.integers(0, len(families), size=len(families)):
                ids.extend(families[int(j)])
        bootstrap.append([np.mean([arrays[cid][k] for cid in ids]) for k in [0, 1]])
    return {
        "candidate": candidate,
        "reference": reference,
        "field": field,
        "n_paired": len(arrays),
        "delta_lower": low,
        "delta_upper": high,
        "positive_favors_candidate": True,
        "interval_95_conservative": [
            float(np.quantile([x[0] for x in bootstrap], 0.025)),
            float(np.quantile([x[1] for x in bootstrap], 0.975)),
        ],
        "bootstrap": "paired family clusters stratified by category; not field-generalization CI",
        "replicates": replicates,
        "seed": seed,
    }


def consolidate(project, version):
    project = Path(project)
    v3 = project / "experimentos/v3"
    dest = v3 / "revisao" / version
    mapping = json.loads((dest / "mapping.json").read_text())
    decisions = [json.loads(s) for s in (dest / "decisions.jsonl").read_text().splitlines()]
    groups = {g["review_id"]: g for g in mapping["groups"]}
    if (
        len(decisions) != len(groups)
        or len({d["review_id"] for d in decisions}) != len(decisions)
        or {d["review_id"] for d in decisions} != set(groups)
    ):
        raise ValueError("Revisão incompleta ou duplicada; não produzir taxas finais.")
    source = project if version == "v2" else v3
    chunks = {
        r["chunk_id"]: r["text"]
        for r in [json.loads(s) for s in (source / "base/chunks.jsonl").read_text().splitlines()]
    }
    originals = {
        mode: {
            r["case_id"]: r
            for r in [
                json.loads(s) for s in (source / "runs" / mode / "responses.jsonl").read_text().splitlines()
            ]
        }
        for mode in {member["mode"] for group in groups.values() for member in group["members"]}
    }
    rows = []
    for d in decisions:
        if d["reviewer_kind"] != "ai_assisted_technical_review" or d["independent_human_review"] is not False:
            raise ValueError("Não apresentar esta anotação por IA como revisão humana.")
        if any(d[f] not in (0, 1, None) for f in FIELDS) or len(d["reason"].strip()) < 20:
            raise ValueError("Julgamento inválido ou sem justificativa.")
        if d["semantic_correct"] == 1 and d["hallucination"] == 1:
            raise ValueError("Acerto semântico não pode coexistir com alucinação anotada.")
        group = groups[d["review_id"]]
        for member in group["members"]:
            original = originals[member["mode"]][member["case_id"]]
            if (
                original["raw"] != group["raw"]
                or [c["chunk_id"] for c in original["chunks"]] != group["context_ids"]
            ):
                raise ValueError("Revisão não corresponde à resposta/contexto original.")
            rows.append(
                {
                    "case_id": member["case_id"],
                    "family": group["family"],
                    "category": group["category"],
                    "mode": member["mode"],
                    **d,
                    **member["structural"],
                    "integral_accuracy": integral_score(member["structural"], d),
                    "new_numeric_tokens_screen": numeric_flags(member, group, chunks),
                    "raw_sha": hashlib.sha256(group["raw"].encode()).hexdigest(),
                }
            )
    if len(rows) != mapping["n_responses"] or len({(r["case_id"], r["mode"]) for r in rows}) != len(rows):
        raise ValueError("Cobertura de respostas divergente.")
    fields = [*FIELDS, "integral_accuracy"]
    report = {
        "version": version,
        "reviewer_kind": "ai_assisted_technical_review",
        "independent_human_review": False,
        "n_responses": len(rows),
        "n_verbatim_context_groups": len(decisions),
        "grouping": "Only same family, exact raw output and identical context IDs share a judgment; questions shown to reviewer.",
        "uncertainty_policy": "Unknown judgments remain in denominators via lower/upper bounds; invalid schema is not automatically hallucination.",
        "limitations": [
            "AI technical annotations, not independent human gold",
            "Synthetic correlated variants; family-cluster intervals do not establish field generalization",
            "Review rationales and raw outputs must remain available for adjudication",
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
            for mode in sorted({r["mode"] for r in rows})
            if (part := [r for r in rows if r["mode"] == mode])
        },
        "comparisons": [
            paired_intervals(rows, a, b, f)
            for a, b in [("final-B", "final-A"), ("final-C", "final-A"), ("final-C", "final-B")]
            for f in ["semantic_correct", "integral_accuracy", "hallucination"]
        ],
        "review_code_sha": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_test_sha": hashlib.sha256((source / "avaliacao/test.jsonl").read_bytes()).hexdigest(),
        "source_chunks_sha": hashlib.sha256((source / "base/chunks.jsonl").read_bytes()).hexdigest(),
        "mapping_sha": hashlib.sha256((dest / "mapping.json").read_bytes()).hexdigest(),
        "decisions_sha": hashlib.sha256((dest / "decisions.jsonl").read_bytes()).hexdigest(),
    }
    with (dest / "reviewed_responses.jsonl").open("x") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with (dest / "metrics.json").open("x") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    with (dest / "reviewed_responses.csv").open("x") as f:
        names = list(dict.fromkeys(key for row in rows for key in row))
        w = csv.DictWriter(f, fieldnames=names)
        w.writeheader()
        w.writerows(rows)
    return report
