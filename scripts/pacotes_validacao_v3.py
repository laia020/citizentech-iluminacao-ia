"""Mostra todas as saídas de famílias de validação, sem acessar o teste."""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "experimentos/v3"


def read(path):
    return [json.loads(s) for s in path.read_text().splitlines()]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--candidate", required=True)
    p.add_argument("--start", type=int, default=0)
    p.add_argument("--count", type=int, default=3)
    p.add_argument("--ids-only", action="store_true")
    args = p.parse_args()
    cases = read(ROOT / "dados/valid.jsonl")
    gold = {r["case_id"]: r for r in cases}
    rows = read(ROOT / "runs" / f"valid-{args.candidate}" / "responses.jsonl")
    families = list(dict.fromkeys(r["scenario_family"] for r in cases))[args.start : args.start + args.count]
    for family in families:
        part = [r for r in rows if r["family"] == family]
        if len(part) != 4:
            raise ValueError("Família ainda incompleta.")
        first = gold[part[0]["case_id"]]
        print(
            json.dumps(
                {"family": family, "input": first["input"], "target": first["target"]}, ensure_ascii=False
            )
        )
        groups = {}
        for row in part:
            key = (row["raw"], tuple(c["chunk_id"] for c in row["chunks"]))
            groups.setdefault(key, []).append(row)
        for (raw, _), group in groups.items():
            print(
                json.dumps(
                    {
                        "case_ids": [r["case_id"] for r in group],
                        "questions": [gold[r["case_id"]]["input"]["pergunta"] for r in group],
                        "context": (
                            [c["chunk_id"] for c in group[0]["chunks"]]
                            if args.ids_only
                            else [{"id": c["chunk_id"], "text": c["text"]} for c in group[0]["chunks"]]
                        ),
                        "raw": raw,
                        "schema_valid": all(r["schema_valid"] for r in group),
                        "status_only_match": all(r["status_only_match"] for r in group),
                    },
                    ensure_ascii=False,
                )
            )


if __name__ == "__main__":
    main()
