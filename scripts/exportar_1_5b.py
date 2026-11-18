"""Preserva evidências pequenas em pastas publicáveis, sem publicar nem gerar resultados."""

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "experimentos/v5-1.5b"


def main():
    selected = json.loads((ROOT / "configs/selected.json").read_text())
    review = json.loads((ROOT / "revisao/test/metrics.json").read_text())
    if review["n_responses"] != 90:
        raise ValueError("Revisão final incompleta.")
    modes = ["final-A", "final-B", "final-C"]
    metrics = {m: json.loads((ROOT / f"runs/{m}/metrics.json").read_text()) for m in modes}
    if any(m["n"] != 30 for m in metrics.values()):
        raise ValueError("Comparação final incompleta.")
    dest = ROOT / "avaliacao/evidencias"
    dest.mkdir(exist_ok=False)
    for name in [*modes, *[f"valid-{c}" for c in selected["candidates"]]]:
        target = dest / name
        target.mkdir()
        for filename in ["responses.jsonl", "metrics.json", "clean_metrics.json"]:
            source = ROOT / "runs" / name / filename
            if source.exists():
                shutil.copy2(source, target / filename)
    for candidate in selected["candidates"]:
        target = ROOT / "avaliacao/treinamento" / candidate
        target.mkdir(parents=True, exist_ok=False)
        for filename in ["summary.json", "provenance.json", "metrics.jsonl"]:
            shutil.copy2(ROOT / "adapters" / candidate / filename, target / filename)
    with (ROOT / "avaliacao/placar.json").open("x") as f:
        json.dump({"generation_metrics": metrics, "technical_content_review": review,
                   "selected_candidate": selected["candidate"], "independent_human_review": False},
                  f, ensure_ascii=False, indent=2)
    print("Respostas brutas, validações, logs pequenos de treino e placar exportados.")


if __name__ == "__main__":
    main()
