"""Conferência final de evidências; sem gerar respostas nem alterar resultados."""

import hashlib
import json
from datetime import datetime
from pathlib import Path

from citizentech_ia.datasets import sha, verify_freeze
from citizentech_ia.v3.analysis_sets import plan
from citizentech_ia.v3.inference import SYSTEM

ROOT = Path(__file__).resolve().parents[1]
V3 = ROOT / "experimentos/v3"


def load(path):
    return json.loads(path.read_text())


def lines(path):
    return [json.loads(s) for s in path.read_text().splitlines()]


def main():
    verify_freeze(V3, system_prompt=SYSTEM)
    verify_freeze(ROOT)
    assert all(sha(V3 / path) == digest for path, digest in load(V3 / "dados/manifest.json")["hashes"].items())
    _, plan_sha = plan(V3)
    sources = load(V3 / "configs/source-snapshot.json")
    assert all(sha(ROOT / path) == digest for path, digest in sources.items()), "Código congelado diverge."
    selection = load(V3 / "configs/selected.json")
    adapter_sha = sha(V3 / selection["adapter_path"] / "adapters.safetensors")
    assert adapter_sha == selection["adapter_sha"]
    assert adapter_sha == load(V3 / "adapters" / selection["candidate"] / "summary.json")["adapter_sha"]
    expected = {r["case_id"] for r in lines(V3 / "avaliacao/test.jsonl")}
    outputs = {
        mode: lines(V3 / "runs" / mode / "responses.jsonl") for mode in ["final-A", "final-B", "final-C"]
    }
    no_ids = 0
    for mode, rows in outputs.items():
        assert len(rows) == 120 and {r["case_id"] for r in rows} == expected
        for row in rows:
            body = json.loads(row["messages"][1]["content"])
            assert set(body) == {"OCORRENCIA", "CONTEXTO"}
            assert not {"ocorrencia_id", "case_id", "category", "split", "scenario_family", "target"} & set(
                body["OCORRENCIA"]
            )
            assert row["case_id"] not in row["messages"][1]["content"]
            assert (
                hashlib.sha256(row["messages"][0]["content"].encode()).hexdigest()
                == hashlib.sha256(SYSTEM.encode()).hexdigest()
            )
            if mode == "final-A":
                assert not row["chunks"]
            no_ids += 1
    b = {r["case_id"]: r for r in outputs["final-B"]}
    assert all(
        r["chunks"] == b[r["case_id"]]["chunks"] and r["messages"] == b[r["case_id"]]["messages"]
        for r in outputs["final-C"]
    )
    metrics = {mode: load(V3 / "runs" / mode / "metrics.json") for mode in outputs}
    assert metrics["final-C"]["model"]["adaptador"] == adapter_sha
    base = V3 / "models/qwen-7b-4bit"
    provenance = load(base / "provenance.json")
    # Weight content is hashed only after timed inference has finished.
    weight_sha = sha(base / "model.safetensors")
    expected_weight_sha = "a7a9fe268352aed9cf26e31f6bdf8f8df26ca63589861dd92f94456ab8554318"
    assert weight_sha == expected_weight_sha
    prepared = load(V3 / "dados/mlx/manifest.json")
    assert all(s["oracle_support_insertions"] == 0 for s in prepared.values())
    reviewed = lines(V3 / "revisao/v3/reviewed_responses.jsonl")
    assert len(reviewed) == len({(r["case_id"], r["mode"]) for r in reviewed}) == 360
    assert all(
        r["reviewer_kind"] == "ai_assisted_technical_review" and r["independent_human_review"] is False
        for r in reviewed
    )
    assert load(V3 / "revisao/v3/clean_metrics.json")["n_responses"] == 336
    api = load(V3 / "docs/regressao-api-real.json")
    assert api["model"]["adaptador"] == adapter_sha
    assert len(api["cases"]) == 13
    notebooks = list((V3 / "notebooks").glob("*.ipynb"))
    assert notebooks
    for path in notebooks:
        cells = load(path)["cells"]
        assert all(c["execution_count"] is not None for c in cells if c["cell_type"] == "code")
        assert not any(o["output_type"] == "error" for c in cells for o in c.get("outputs", []))
    report = {
        "verified_at": datetime.now().astimezone().isoformat(),
        "v2_data_freeze_preserved": True,
        "v3_data_prompt_freeze_preserved": True,
        "frozen_prediction_sources_unchanged": True,
        "prompts_checked_without_control_ids": no_ids,
        "B_C_contexts_and_messages_identical": True,
        "same_base_weights_sha": weight_sha,
        "model_revision": provenance,
        "adapter_selected_evaluated_served_sha": adapter_sha,
        "analysis_plan_sha": plan_sha,
        "static_test_retrieval_coverage_inspected_before_selection": True,
        "coverage_audit_deviation": load(V3 / "configs/coverage_audit_deviation.json"),
        "all_raw_responses_reviewed": 360,
        "confirmatory_responses_reviewed": 336,
        "independent_human_review": False,
        "notebooks_executed_without_errors": len(notebooks),
        "api_http_statuses": {c["case"]: c["http_status"] for c in api["cases"]},
        "api_semantic_correctness": "see separate technical review; HTTP status is not semantic accuracy",
        "external_integration_completed": False,
        "published": False,
        "visual_browser_validation": "pending; prior origin approval denied, no bypass",
    }
    with (V3 / "docs/validacao-revisao.json").open("x") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(
        json.dumps({k: v for k, v in report.items() if k != "model_revision"}, ensure_ascii=False, indent=2)
    )


if __name__ == "__main__":
    main()
