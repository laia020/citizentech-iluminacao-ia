"""Compara a correção com o serviço original em casos separados, sem treinar."""

import json
import time
from pathlib import Path

from citizentech_ia.datasets import read_jsonl, sha, verify_freeze
from citizentech_ia.evaluation import grade_structure
from citizentech_ia.schemas import Occurrence
from citizentech_ia.v5.inference import SYSTEM as OLD_SYSTEM
from citizentech_ia.v5.inference import Analyzer, Generator
from citizentech_ia.v5.pipeline import retriever as old_retriever
from citizentech_ia.v6.inference import GroundedAnalyzer, retriever
from citizentech_ia.v6.service import verify_runtime


def main():
    root = Path(__file__).resolve().parents[1]
    baseline, revision = root / "experimentos/v5-1.5b", root / "experimentos/v6-fundamentacao"
    verify_freeze(baseline, system_prompt=OLD_SYSTEM)
    verify_runtime(revision)
    selected = json.loads((baseline / "configs/selected.json").read_text())
    adapter = baseline / selected["adapter_path"]
    assert sha(adapter / "adapters.safetensors") == selected["adapter_sha"]
    generator = Generator(baseline / "models/qwen-1.5b-fp16", adapter)
    analyzers = {
        "v5_original": Analyzer(generator, old_retriever(baseline), threshold=0.11),
        "v6_candidate": GroundedAnalyzer(generator, retriever(read_jsonl(revision / "base/chunks.jsonl")), threshold=0.11),
    }
    for name, path in [("desenvolvimento", "dados/desenvolvimento.jsonl"), ("adicional", "avaliacao/adicional.jsonl")]:
        with (revision / "runs" / f"{name}.jsonl").open("x") as f:
            for case in read_jsonl(revision / path):
                occurrence = Occurrence.model_validate(case["input"])
                for mode, analyzer in analyzers.items():
                    messages, chunks, tokens = analyzer.prepare(occurrence)
                    started = time.perf_counter()
                    raw = generator.generate(messages, max_tokens=512)
                    structure = grade_structure(analyzer, raw, chunks, occurrence, case["expected_status"])
                    row = {
                        "id": case["id"], "mode": mode, "input": case["input"], "raw": raw,
                        "messages": messages, "chunks": chunks, "input_tokens": tokens,
                        "seconds": time.perf_counter() - started, **structure, "model": generator.metadata(),
                    }
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
                    f.flush()
                    print(json.dumps({"set": name, "id": case["id"], "mode": mode, **structure}), flush=True)
    print("COMPARISON_DONE", flush=True)


if __name__ == "__main__":
    main()
