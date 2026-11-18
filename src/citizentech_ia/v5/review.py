"""Anotação explícita de respostas; não classifica conteúdo por palavras-chave."""

import hashlib
import json
from pathlib import Path

from ..datasets import read_jsonl, sha, write_jsonl
from ..v3.review_metrics import FIELDS, integral_score, metric_bounds, paired_intervals


def build(root, phase, runs):
    root = Path(root)
    dest = root / "revisao" / phase
    dest.mkdir(exist_ok=False)
    groups = {}
    families = []
    sources = {}
    for run in runs:
        path = root / "runs" / run / "responses.jsonl"
        metrics = json.loads((path.parent / "metrics.json").read_text())
        rows = read_jsonl(path)
        if len(rows) != metrics["n"]:
            raise ValueError("Execução incompleta.")
        sources[run] = sha(path)
        for row in rows:
            body = json.loads(row["messages"][1]["content"])["OCORRENCIA"]
            context = [c["chunk_id"] for c in row["chunks"]]
            key = json.dumps([row["family"], row["raw"], context], ensure_ascii=False)
            uid = hashlib.sha256(key.encode()).hexdigest()[:12]
            if row["family"] not in families:
                families.append(row["family"])
            if uid not in groups:
                groups[uid] = {
                    "review_id": uid, "family": row["family"], "category": row["category"],
                    "raw": row["raw"], "context_ids": context, "members": [],
                }
            groups[uid]["members"].append({
                "run": run, "case_id": row["case_id"], "input": body,
                "structural": {k: row[k] for k in ["schema_valid", "valid_json_and_refs"]},
            })
    mapping = {
        "phase": phase, "runs": runs, "source_hashes": sources,
        "families": families, "groups": list(groups.values()),
        "n_responses": sum(len(g["members"]) for g in groups.values()),
        "reviewer_kind": "ai_assisted_technical_review", "independent_human_review": False,
        "limitations": "Mode hidden in packets but style may reveal it; related AI authorship/review; synthetic cases.",
    }
    with (dest / "mapping.json").open("x") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    return {"families": len(families), "groups": len(groups), "responses": mapping["n_responses"]}


def packet(root, phase, start, count):
    root = Path(root)
    m = json.loads((root / "revisao" / phase / "mapping.json").read_text())
    targets = {
        r["case_id"]: r["target"]
        for r in read_jsonl(root / ("dados/valid.jsonl" if phase.startswith("valid-") else "avaliacao/test.jsonl"))
    }
    result = []
    for index, family in enumerate(m["families"][start:start + count], start):
        gs = [g for g in m["groups"] if g["family"] == family]
        inputs = [member["input"] for g in gs for member in g["members"]]
        observations = [{k: v for k, v in inp.items() if k != "pergunta"} for inp in inputs]
        common = all(x == observations[0] for x in observations)
        result.append({
            "index": index, "family": family, "category": gs[0]["category"],
            "observations": observations[0] if common else "see individual inputs",
            "reference_target_not_infallible": targets[gs[0]["members"][0]["case_id"]],
            "groups": [{
                "id": g["review_id"], "n": len(g["members"]),
                "questions": list(dict.fromkeys(member["input"]["pergunta"] for member in g["members"])),
                **({} if common else {"inputs": [member["input"] for member in g["members"]]}),
                "context": g["context_ids"], "raw": g["raw"],
            } for g in gs],
        })
    return result


def append(root, phase, entries):
    dest = Path(root) / "revisao" / phase
    m = json.loads((dest / "mapping.json").read_text())
    allowed = {g["review_id"] for g in m["groups"]}
    p = dest / "decisions.jsonl"
    known = {d["review_id"] for d in read_jsonl(p)} if p.exists() else set()
    with p.open("a") as f:
        for uid, flags, reason in entries:
            if uid not in allowed or uid in known or len(flags) != 4:
                raise ValueError("Anotação desconhecida, duplicada ou inválida.")
            if any(x not in [0, 1, None] for x in flags) or len(reason.strip()) < 20:
                raise ValueError("Julgamento exige flags e justificativa explícitas.")
            if flags[0] == flags[1] == 1:
                raise ValueError("Acerto não coexiste com alucinação anotada.")
            f.write(json.dumps({
                "review_id": uid, **dict(zip(FIELDS, flags)), "reason": reason,
                "reviewer_kind": "ai_assisted_technical_review", "independent_human_review": False,
            }, ensure_ascii=False) + "\n")
            known.add(uid)
    return len(known), len(allowed)


def reuse_exact(root, source_phase, destination_phase):
    """Reaproveita só julgamento explícito com entrada, texto e contexto idênticos."""
    root = Path(root)
    source = root / "revisao" / source_phase
    dest = root / "revisao" / destination_phase
    a = json.loads((source / "mapping.json").read_text())
    b = json.loads((dest / "mapping.json").read_text())
    groups = {g["review_id"]: g for g in a["groups"]}
    decisions = {d["review_id"]: d for d in read_jsonl(source / "decisions.jsonl")}
    entries = []
    for g in b["groups"]:
        old = groups.get(g["review_id"])
        if old is None or old["raw"] != g["raw"] or old["context_ids"] != g["context_ids"]:
            continue
        inputs = {(m["case_id"], json.dumps(m["input"], sort_keys=True)) for m in old["members"]}
        if not all((m["case_id"], json.dumps(m["input"], sort_keys=True)) in inputs for m in g["members"]):
            continue
        d = decisions[g["review_id"]]
        entries.append((g["review_id"], [d[f] for f in FIELDS], d["reason"] +
                        " Julgamento reutilizado: entrada, saída bruta e contexto exatamente iguais à revisão anterior."))
    result = append(root, destination_phase, entries)
    with (dest / "reused_exact_judgments.json").open("x") as f:
        json.dump({"source_phase": source_phase, "source_decisions_sha": sha(source / "decisions.jsonl"),
                   "ids": [x[0] for x in entries], "matching": "exact case/input/raw/context; no semantic classifier"},
                  f, ensure_ascii=False, indent=2)
    return result


def consolidate(root, phase):
    root = Path(root)
    dest = root / "revisao" / phase
    m = json.loads((dest / "mapping.json").read_text())
    decisions = read_jsonl(dest / "decisions.jsonl")
    groups = {g["review_id"]: g for g in m["groups"]}
    if len(decisions) != len(groups) or {d["review_id"] for d in decisions} != set(groups):
        raise ValueError("Revisão incompleta ou duplicada.")
    for run, digest in m["source_hashes"].items():
        if sha(root / "runs" / run / "responses.jsonl") != digest:
            raise ValueError("As saídas brutas mudaram.")
    rows = []
    for d in decisions:
        g = groups[d["review_id"]]
        for member in g["members"]:
            rows.append({
                **d, "mode": member["run"], "case_id": member["case_id"],
                "family": g["family"], "category": g["category"], **member["structural"],
                "integral_accuracy": integral_score(member["structural"], d),
                "raw_sha": hashlib.sha256(g["raw"].encode()).hexdigest(),
            })
    if len(rows) != m["n_responses"] or len({(r["case_id"], r["mode"]) for r in rows}) != len(rows):
        raise ValueError("Cobertura divergente.")
    report = {
        "reviewer_kind": "ai_assisted_technical_review", "independent_human_review": False,
        "n_responses": len(rows), "n_groups": len(groups),
        "limitations": m["limitations"], "mapping_sha": sha(dest / "mapping.json"),
        "decisions_sha": sha(dest / "decisions.jsonl"),
        "modes": {run: {
            "n": len(part),
            **{key: metric_bounds([r[key] for r in part]) for key in [*FIELDS, "integral_accuracy"]},
            "by_category": {cat: {
                key: metric_bounds([r[key] for r in part if r["category"] == cat])
                for key in [*FIELDS, "integral_accuracy"]
            } for cat in sorted({r["category"] for r in part})},
        } for run in m["runs"] if (part := [r for r in rows if r["mode"] == run])},
    }
    if phase == "test":
        report["comparisons"] = [
            paired_intervals(rows, a, b, field)
            for a, b in [("final-B", "final-A"), ("final-C", "final-A"), ("final-C", "final-B")]
            for field in ["semantic_correct", "integral_accuracy", "hallucination"]
        ]
    write_jsonl(dest / "reviewed_responses.jsonl", rows)
    with (dest / "metrics.json").open("x") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return report
