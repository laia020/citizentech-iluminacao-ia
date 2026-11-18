import json
from pathlib import Path
from statistics import mean

from .datasets import read_jsonl, sha
from .inference import retrieval_query
from .retrieval import Retriever, calibrate, retrieval_metrics
from .schemas import Occurrence


def load_retriever(root):
    return Retriever(read_jsonl(Path(root) / "base/chunks.jsonl"))


def calibrate_retrieval(root):
    root = Path(root)
    r = load_retriever(root)
    records = []
    calibration = []
    for row in read_jsonl(root / "dados/valid.jsonl"):
        inp = Occurrence.model_validate(row["input"])
        hits = r.search(retrieval_query(inp), municipality=inp.municipio, threshold=0)
        records.append(
            {
                "case_id": row["case_id"],
                **retrieval_metrics([h["chunk_id"] for h in hits], row["relevant_chunks"]),
            }
        )
        calibration.append(
            {
                "split": "valid",
                "score": hits[0]["score"] if hits else 0,
                "answerable": row["category"] == "respondivel",
            }
        )
    result = calibrate(calibration)
    result["metrics_valid"] = {
        k: mean(row[k] for row in records if row[k] is not None)
        for k in ["recall@1", "recall@3", "hit@1", "hit@3"]
    }
    result["base_sha"] = sha(root / "base/chunks.jsonl")
    result["valid_sha"] = sha(root / "dados/valid.jsonl")
    result["records"] = records
    # This threshold governs retrieval evidence, not a calibrated probability of answer correctness.
    (root / "configs/retrieval.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
    return result
