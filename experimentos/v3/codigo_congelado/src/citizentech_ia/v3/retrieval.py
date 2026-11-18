from statistics import mean

import numpy as np

from ..retrieval import Retriever, retrieval_metrics


def query(occurrence):
    return " ".join(
        [
            *([occurrence.pergunta] * 3),
            occurrence.relato,
            *[f"{s.tipo} {s.unidade} calibração declarada {s.calibrado}" for s in occurrence.sensores],
            *[v.descricao for v in occurrence.observacoes_visuais],
        ]
    )


class ReviewedRetriever(Retriever):
    def __init__(self, chunks):
        indexed = [{**c, "text": c["text"] + " " + c.get("retrieval_terms", "")} for c in chunks]
        super().__init__(indexed)
        # Search returns the source itself; lexical aliases are not quoted as documentary evidence.
        self.chunks = chunks


def calibrate_relevance(rows, min_recall=0.95):
    if not rows or any(r["split"] != "valid" for r in rows):
        raise ValueError("Calibração exige somente validação não vazia.")
    candidates = []
    for threshold in np.linspace(0, 1, 101):
        recalls, tp, fp, returned = [], 0, 0, 0
        for row in rows:
            selected = [h["chunk_id"] for h in row["ranked"] if h["score"] + 1e-12 >= threshold][:3]
            relevant = set(row["relevant"])
            metric = retrieval_metrics(selected, relevant)["recall@3"]
            if metric is not None:
                recalls.append(metric)
            tp += len(set(selected) & relevant)
            fp += len(set(selected) - relevant)
            returned += len(selected)
        recall = mean(recalls) if recalls else 0
        precision = tp / returned if returned else 0
        candidates.append(
            {
                "threshold": float(threshold),
                "recall_at_3": recall,
                "precision_at_3": precision,
                "true_retrieved_chunks": tp,
                "false_retrieved_chunks": fp,
                "recall_target_met": recall >= min_recall,
            }
        )
    feasible = [c for c in candidates if c["recall_target_met"]]
    chosen = max(
        feasible or candidates,
        key=lambda c: (
            c["precision_at_3"] if feasible else c["recall_at_3"],
            c["recall_at_3"] if feasible else c["precision_at_3"],
            c["threshold"],
        ),
    )
    return {
        **chosen,
        "calibration_target": "relevant_chunks_not_answerability",
        "minimum_macro_recall": min_recall,
        "n_validation_queries": len(rows),
        "grid": candidates,
    }
