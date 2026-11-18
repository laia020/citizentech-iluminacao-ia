import copy
import hashlib
import json
from pathlib import Path
from statistics import mean

from ..datasets import read_jsonl, sha, write_jsonl
from ..retrieval import retrieval_metrics
from ..schemas import Occurrence
from ..v3.retrieval import ReviewedRetriever, calibrate_relevance, query
from .inference import SYSTEM, Analyzer


def retriever(root):
    return ReviewedRetriever(read_jsonl(Path(root) / "base/chunks.jsonl"))


def calibrate(root):
    root = Path(root)
    r = retriever(root)
    rows = []
    for row in read_jsonl(root / "dados/valid.jsonl"):
        inp = Occurrence.model_validate(row["input"])
        rows.append(
            {
                "case_id": row["case_id"],
                "split": "valid",
                "relevant": row["relevant_chunks"],
                "ranked": r.search(query(inp), municipality=inp.municipio, threshold=0, k=len(r.chunks)),
            }
        )
    result = calibrate_relevance(rows)
    result["records"] = [
        {
            "case_id": row["case_id"],
            **retrieval_metrics(
                [h["chunk_id"] for h in row["ranked"] if h["score"] + 1e-12 >= result["threshold"]][:3],
                row["relevant"],
            ),
        }
        for row in rows
    ]
    result["metrics_valid"] = {
        key: mean(x[key] for x in result["records"] if x[key] is not None) for key in ["recall@1", "recall@3"]
    }
    result["base_sha"], result["valid_sha"] = sha(root / "base/chunks.jsonl"), sha(root / "dados/valid.jsonl")
    with (root / "configs/retrieval.json").open("x") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return result


def prepare(root):
    from transformers import AutoTokenizer

    root = Path(root)
    tokenizer = AutoTokenizer.from_pretrained(
        str(root / json.loads((root / "configs/model.json").read_text())["model_path"]), local_files_only=True
    )

    class Counter:
        def count_messages(self, messages):
            return len(
                tokenizer.apply_chat_template(
                    messages, tokenize=True, add_generation_prompt=True, return_dict=False
                )
            )

    threshold = json.loads((root / "configs/retrieval.json").read_text())["threshold"]
    a = Analyzer(Counter(), retriever(root), threshold=threshold)
    dest = root / "dados/mlx"
    dest.mkdir(exist_ok=False)
    stats = {}
    for split in ["train", "valid"]:
        examples, lengths, misses, no_refs = [], [], 0, 0
        for row in read_jsonl(root / f"dados/{split}.jsonl"):
            messages, chunks, _ = a.prepare(Occurrence.model_validate(row["input"]))
            available = {c["chunk_id"] for c in chunks}
            target = copy.deepcopy(row["target"])
            support = set(row["relevant_chunks"])
            misses += not bool(support & available)
            # Never insert the expected chunk. Citations may only refer to actual retrieved passages.
            target["fontes"] = [cid for cid in row["target"]["fontes"] if cid in available]
            no_refs += not bool(target["fontes"])
            messages.append({"role": "assistant", "content": json.dumps(target, ensure_ascii=False)})
            n = len(tokenizer.apply_chat_template(messages, tokenize=True, return_dict=False))
            if n > 2048:
                raise ValueError(f"Exemplo excede contexto: {row['case_id']}")
            examples.append({"messages": messages})
            lengths.append(n)
        write_jsonl(dest / f"{split}.jsonl", examples)
        stats[split] = {
            "n": len(examples),
            "max_tokens": max(lengths),
            "mean_tokens": mean(lengths),
            "retrieval_misses_recorded": misses,
            "targets_without_citations": no_refs,
            "oracle_support_insertions": 0,
            "sha": sha(dest / f"{split}.jsonl"),
        }
    (dest / "manifest.json").write_text(json.dumps(stats, indent=2))
    return stats


def freeze(root):
    root = Path(root)
    paths = [
        root / "dados/manifest.json",
        root / "dados/mlx/train.jsonl",
        root / "dados/mlx/valid.jsonl",
        root / "dados/mlx/manifest.json",
        root / "dados/train.jsonl",
        root / "dados/valid.jsonl",
        root / "avaliacao/test.jsonl",
        root / "base/chunks.jsonl",
        root / "base/catalogo.jsonl",
        root / "configs/retrieval.json",
        root / "configs/protocol.json",
        root / "configs/model.json",
        root / "configs/clean_holdout_plan.json",
        root / "configs/clean_holdout_freeze.json",
    ]
    result = {
        "artifacts": {str(p.relative_to(root)): sha(p) for p in paths},
        "prompt_version": "v4-light-same-reviewed-policy-no-oracle",
        "system_sha": hashlib.sha256(SYSTEM.encode()).hexdigest(),
    }
    with (root / "configs/frozen_manifest.json").open("x") as f:
        json.dump(result, f, indent=2)
    return result
