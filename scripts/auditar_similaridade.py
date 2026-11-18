"""Audita semelhança textual sem alterar dados, limiar ou seleção de modelos."""

import json
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from citizentech_ia.datasets import read_jsonl, verify_freeze

ROOT = Path(__file__).resolve().parents[1]


def main():
    verify_freeze(ROOT)
    groups = {
        split: read_jsonl(ROOT / path)
        for split, path in {
            "train": "dados/train.jsonl",
            "valid": "dados/valid.jsonl",
            "test": "avaliacao/test.jsonl",
        }.items()
    }
    rows = [r for group in groups.values() for r in group]
    # Only natural-language evidence/question: identifiers and gold labels are excluded.
    texts = [r["input"].get("relato", "") + " " + r["input"]["pergunta"] for r in rows]
    vectors = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5)).fit_transform(texts)
    offsets, start = {}, 0
    for split, group in groups.items():
        offsets[split] = (start, start + len(group))
        start += len(group)
    report = {
        "method": "TF-IDF char_wb 3–5; cosine; relato+pergunta; no gold labels; descriptive audit only",
        "limitation": "Semelhança textual não certifica independência semântica. Nenhum dado ou hiperparâmetro foi alterado com este relatório.",
        "comparisons": {},
    }
    for left, right in [("valid", "train"), ("test", "train"), ("test", "valid")]:
        a, b = offsets[left], offsets[right]
        scores = cosine_similarity(vectors[a[0] : a[1]], vectors[b[0] : b[1]])
        nearest = scores.argmax(axis=1)
        maxima = scores.max(axis=1)
        pairs = sorted(
            [
                {
                    "left_case": groups[left][i]["case_id"],
                    "right_case": groups[right][int(j)]["case_id"],
                    "cosine": float(maxima[i]),
                }
                for i, j in enumerate(nearest)
            ],
            key=lambda item: -item["cosine"],
        )
        report["comparisons"][f"{left}_vs_{right}"] = {
            "n_left": len(maxima),
            "max_cosine": float(maxima.max()),
            "mean_nearest_cosine": float(maxima.mean()),
            "left_cases_above": {str(t): int((maxima >= t).sum()) for t in [0.8, 0.9, 0.95]},
            "top_10_pairs": pairs[:10],
        }
    path = ROOT / "docs/auditoria-similaridade.json"
    with path.open("x") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
