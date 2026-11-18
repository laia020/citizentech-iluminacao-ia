"""Confere evidências finais sem executar LLM ou alterar resultados."""

import hashlib
import json
from pathlib import Path

from citizentech_ia.datasets import read_jsonl, sha, verify_freeze
from citizentech_ia.v5.inference import SYSTEM

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "experimentos/v5-1.5b"


def load(path):
    return json.loads((RUN / path).read_text())


def main():
    verify_freeze(RUN, system_prompt=SYSTEM)
    verify_freeze(ROOT)
    source_hashes = load("configs/source-snapshot.json")
    ui = "src/citizentech_ia/v5/demo.html"
    assert all(sha(ROOT / p) == digest for p, digest in source_hashes.items() if p != ui)
    selection = load("configs/selected.json")
    adapter = RUN / selection["adapter_path"]
    adapter_sha = sha(adapter / "adapters.safetensors")
    assert adapter_sha == selection["adapter_sha"]
    assert adapter_sha == load(f"adapters/{selection['candidate']}/summary.json")["adapter_sha"]
    expected = {r["case_id"] for r in read_jsonl(RUN / "avaliacao/test.jsonl")}
    outputs = {m: read_jsonl(RUN / "runs" / m / "responses.jsonl") for m in ["final-A", "final-B", "final-C"]}
    checked = 0
    for mode, rows in outputs.items():
        assert len(rows) == 30 and {r["case_id"] for r in rows} == expected
        for row in rows:
            body = json.loads(row["messages"][1]["content"])
            assert set(body) == {"OCORRENCIA", "CONTEXTO"}
            assert not {"ocorrencia_id", "case_id", "scenario_family", "split", "category", "target", "origin"} & set(body["OCORRENCIA"])
            assert row["case_id"] not in row["messages"][1]["content"]
            assert row["messages"][0]["content"] == SYSTEM
            if mode == "final-A":
                assert row["chunks"] == []
            checked += 1
    b = {r["case_id"]: r for r in outputs["final-B"]}
    assert all(r["messages"] == b[r["case_id"]]["messages"] and r["chunks"] == b[r["case_id"]]["chunks"] for r in outputs["final-C"])
    model = load("runs/final-C/metrics.json")["model"]
    assert model["modelo"] == "Qwen/Qwen2.5-1.5B-Instruct" and model["adaptador"] == adapter_sha
    reviewed = read_jsonl(RUN / "revisao/test/reviewed_responses.jsonl")
    assert len(reviewed) == len({(r["mode"], r["case_id"]) for r in reviewed}) == 90
    assert all(r["independent_human_review"] is False for r in reviewed)
    originals = {m: {r["case_id"]: r for r in rows} for m, rows in outputs.items()}
    assert all(hashlib.sha256(originals[r["mode"]][r["case_id"]]["raw"].encode()).hexdigest() == r["raw_sha"] for r in reviewed)
    for mode in outputs:
        for filename in ["responses.jsonl", "metrics.json"]:
            assert (RUN / f"runs/{mode}/{filename}").read_bytes() == (RUN / f"avaliacao/evidencias/{mode}/{filename}").read_bytes()
    api = load("docs/teste-poc-real.json")
    assert api["model"]["adaptador"] == adapter_sha
    notebook = load("notebooks/06_treinamento_e_avaliacao_1_5b.ipynb")
    assert all(c["execution_count"] is not None for c in notebook["cells"] if c["cell_type"] == "code")
    assert not any(o["output_type"] == "error" for c in notebook["cells"] for o in c.get("outputs", []))
    base = RUN / load("configs/model.json")["model_path"]
    provenance = json.loads((base / "provenance.json").read_text())
    with (base / "model.safetensors").open("rb") as f:
        base_sha = hashlib.file_digest(f, "sha256").hexdigest()
    assert base_sha == provenance["files"]["model.safetensors"]
    result = {
        "date": "2026-11-17", "model": model,
        "data_and_prompt_frozen": True, "v2_data_freeze_preserved": True,
        "frozen_prediction_sources_unchanged": True,
        "ui_asset_updated_after_training": sha(ROOT / ui) != source_hashes[ui],
        "ui_original_sha": source_hashes[ui], "ui_current_sha": sha(ROOT / ui),
        "prompts_checked_without_control_ids": checked, "B_C_inputs_contexts_identical": True,
        "base_weight_sha": base_sha, "selected_evaluated_served_adapter_sha": adapter_sha,
        "technical_ai_reviews": 90, "independent_human_review": False,
        "notebook_executed_without_errors": True, "portable_exports_identical": True,
        "poc_http_statuses": [c["http_status"] for c in api["cases"]],
        "public_deploy": False, "group_integration": False,
        "visual_browser_review": "pending; prior refusal not bypassed",
    }
    with (RUN / "docs/VALIDACAO-FINAL.json").open("x") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
