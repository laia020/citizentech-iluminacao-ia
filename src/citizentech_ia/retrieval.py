import unicodedata

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


def normalize(text):
    return " ".join(unicodedata.normalize("NFKC", text).lower().split())


class Retriever:
    def __init__(self, chunks):
        if not chunks or len({c["chunk_id"] for c in chunks}) != len(chunks):
            raise ValueError("Base vazia ou IDs duplicados.")
        self.chunks = chunks
        texts = [normalize(c["text"]) for c in chunks]
        self.word = TfidfVectorizer(ngram_range=(1, 2), norm="l2")
        self.char = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), norm="l2")
        self.w = self.word.fit_transform(texts)
        self.c = self.char.fit_transform(texts)

    def search(self, query, municipality=None, threshold=0.0, k=3):
        query = normalize(query)
        scores = (
            (self.w @ self.word.transform([query]).T).toarray().ravel()
            + (self.c @ self.char.transform([query]).T).toarray().ravel()
        ) / 2
        hits = []
        for chunk, score in zip(self.chunks, scores):
            jurisdiction = chunk.get("jurisdiction")
            allowed = not jurisdiction or (
                municipality and normalize(jurisdiction) == normalize(municipality)
            )
            if allowed and float(score) >= threshold:
                hits.append({**chunk, "score": float(score)})
        return sorted(hits, key=lambda h: (-h["score"], h["chunk_id"]))[:k]


def retrieval_metrics(ranked, relevant):
    relevant = set(relevant)
    out = {}
    for k in (1, 3):
        found = len(set(ranked[:k]) & relevant)
        out[f"recall@{k}"] = found / len(relevant) if relevant else None
        out[f"hit@{k}"] = int(found > 0) if relevant else None
    return out


def calibrate(rows):
    if not rows or any(r["split"] != "valid" for r in rows):
        raise ValueError("Calibração exige exclusivamente validação não vazia.")
    best = None
    for threshold in np.linspace(0, 1, 101):
        tp = fp = fn = 0
        for r in rows:
            predicted = r["score"] >= threshold
            tp += predicted and r["answerable"]
            fp += predicted and not r["answerable"]
            fn += not predicted and r["answerable"]
        f1 = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0
        key = (f1, -fp, float(threshold))
        if best is None or key > best[0]:
            best = (
                key,
                {"threshold": float(threshold), "f1": f1, "tp": int(tp), "fp": int(fp), "fn": int(fn)},
            )
    return best[1]
