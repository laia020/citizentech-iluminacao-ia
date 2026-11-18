"""Pacotes de revisão técnica com modos ocultos e respostas idênticas agrupadas."""

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V3 = ROOT / "experimentos/v3"


def build(version):
    source = ROOT if version == "v2" else V3
    gold = {r["case_id"]: r for r in read(source / "avaliacao/test.jsonl")}
    modes = ["final-A", "final-B", "final-C"]
    groups = {}
    for mode in modes:
        path = source / "runs" / mode / "responses.jsonl"
        for row in read(path):
            item = gold[row["case_id"]]
            context = tuple(c["chunk_id"] for c in row["chunks"])
            family = item["scenario_family"]
            key = (family, row["raw"], context)
            if key not in groups:
                uid = hashlib.sha256(repr((version, key)).encode()).hexdigest()[:12]
                groups[key] = {
                    "review_id": uid,
                    "family": family,
                    "category": item["category"],
                    "raw": row["raw"],
                    "context_ids": list(context),
                    "members": [],
                }
            groups[key]["members"].append(
                {
                    "mode": mode,
                    "case_id": row["case_id"],
                    "input": item["input"],
                    "gold": item["target"],
                    "structural": {k: row[k] for k in ["schema_valid", "valid_json_and_refs"]},
                }
            )
    dest = V3 / "revisao" / version
    dest.mkdir(parents=True, exist_ok=True)
    values = sorted(groups.values(), key=lambda x: x["review_id"])
    families = list(dict.fromkeys(x["scenario_family"] for x in gold.values()))
    mapping = {
        "version": version,
        "n_responses": sum(len(g["members"]) for g in values),
        "n_groups": len(values),
        "families": families,
        "groups": values,
        "grouping_rule": "same family, verbatim raw response and identical received context IDs; no mode-based scoring",
        "reviewer_kind": "ai_assisted_technical_review",
        "independent_human_review": False,
    }
    with (dest / "mapping.json").open("x") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    return mapping


def read(path):
    return [json.loads(s) for s in path.read_text().splitlines() if s.strip()]


def packet(version, start, count):
    p = V3 / "revisao" / version / "mapping.json"
    mapping = json.loads(p.read_text()) if p.exists() else build(version)
    families = mapping["families"][start : start + count]
    for family in families:
        groups = [g for g in mapping["groups"] if g["family"] == family]
        first = groups[0]["members"][0]
        inp = {k: v for k, v in first["input"].items() if k not in ["pergunta", "ocorrencia_id"]}
        print(
            json.dumps(
                {
                    "FAMILY": family,
                    "category": groups[0]["category"],
                    "observations": inp,
                    "reference_target": first["gold"],
                    "note": "Alvo pode ter ambiguidade; avaliar pergunta específica, não exigir texto idêntico.",
                },
                ensure_ascii=False,
            )
        )
        for group in groups:
            questions = sorted({m["input"]["pergunta"] for m in group["members"]})
            print(
                json.dumps(
                    {
                        "review_id": group["review_id"],
                        "n": len(group["members"]),
                        "questions": questions,
                        "context": group["context_ids"],
                        "raw": group["raw"],
                        "schema_valid": all(m["structural"]["schema_valid"] for m in group["members"]),
                        "refs_valid": all(m["structural"]["valid_json_and_refs"] for m in group["members"]),
                    },
                    ensure_ascii=False,
                )
            )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--version", choices=["v2", "v3"], required=True)
    p.add_argument("--start", type=int, default=0)
    p.add_argument("--count", type=int, default=3)
    a = p.parse_args()
    packet(a.version, a.start, a.count)
