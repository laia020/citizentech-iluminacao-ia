"""Registra seleção por validação antes do teste, preservando todos os candidatos."""

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

from citizentech_ia.datasets import sha
from citizentech_ia.v3.analysis_sets import plan

ROOT = Path(__file__).resolve().parents[1] / "experimentos/v3"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", nargs="+", required=True)
    parser.add_argument("--validation-review", type=Path, required=True)
    args = parser.parse_args()
    _, plan_sha = plan(ROOT)
    if any((ROOT / "runs" / name).exists() for name in ["final-A", "final-B", "final-C"]):
        raise ValueError("Teste já aberto; não selecionar novamente com este protocolo.")
    review = json.loads(args.validation_review.read_text())
    if review["reviewer_kind"] != "ai_assisted_technical_review" or review["independent_human_review"]:
        raise ValueError("Identificar corretamente o tipo de revisão.")
    candidates = {}
    for name in args.candidates:
        summary = json.loads((ROOT / "adapters" / name / "summary.json").read_text())
        metrics_path = ROOT / "runs" / f"valid-{name}" / "clean_metrics.json"
        metrics = json.loads(metrics_path.read_text())
        validation_path = ROOT / "runs" / f"valid-{name}" / "responses.jsonl"
        expected_ids = {json.loads(s)["case_id"] for s in validation_path.read_text().splitlines()}
        reviewed = review["candidates"][name]
        if set(reviewed["reviewed_case_ids"]) != expected_ids or len(expected_ids) != 80:
            raise ValueError("Revisão deve cobrir todas as respostas de validação.")
        if summary["microsteps"] != 800 or not summary["adapters_changed"] or metrics["plan_sha"] != plan_sha:
            raise ValueError("Treino ou conjunto de seleção divergente do adendo.")
        if metrics["model"]["adaptador"] != sha(ROOT / "adapters" / name / "adapters.safetensors"):
            raise ValueError("Validação diverge dos pesos finais.")
        candidates[name] = {
            "clean_metrics": metrics,
            "summary": summary,
            "metrics_sha": sha(metrics_path),
            "validation_responses_sha": sha(validation_path),
            "technical_problem": reviewed["technical_problem"],
        }
    r1 = candidates["r1"]
    needs_second = (
        r1["clean_metrics"]["schema_valid_rate"] < 0.95
        or r1["clean_metrics"]["status_only_match_rate"] < 0.90
        or r1["technical_problem"]
    )
    if needs_second and "r2" not in candidates:
        raise ValueError("Condição predefinida exige avaliar o segundo candidato antes da seleção.")
    chosen = max(
        candidates,
        key=lambda name: (
            candidates[name]["clean_metrics"]["status_only_match_rate"],
            candidates[name]["clean_metrics"]["valid_json_and_refs_rate"],
            candidates[name]["clean_metrics"]["schema_valid_rate"],
            -candidates[name]["clean_metrics"]["median_seconds"],
        ),
    )
    destination = ROOT / "adapters/selected/final"
    destination.mkdir(parents=True, exist_ok=False)
    for filename in ["adapter_config.json", "adapters.safetensors"]:
        shutil.copy2(ROOT / "adapters" / chosen / filename, destination / filename)
    result = {
        "selected_at": datetime.now().astimezone().isoformat(),
        "candidate": chosen,
        "checkpoint": "final weights, exactly 800 microsteps / 200 updates",
        "adapter_path": "adapters/selected/final",
        "adapter_sha": sha(destination / "adapters.safetensors"),
        "plan_sha": plan_sha,
        "second_candidate_condition_met": needs_second,
        "criterion": "clean validation: pure status, valid schema/references, schema, latency; lexicographic",
        "candidates": candidates,
        "validation_review_sha": sha(args.validation_review),
        "test_used_for_selection": False,
        "independent_human_review": False,
    }
    with (ROOT / "configs/selected.json").open("x") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(chosen, result["adapter_sha"])


if __name__ == "__main__":
    main()
