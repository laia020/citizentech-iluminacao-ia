import json

import pytest

from citizentech_ia.v5.review import reuse_exact


@pytest.mark.parametrize("changed_input,expected", [(False, 1), (True, 0)])
def test_revisao_so_e_reutilizada_quando_a_observacao_tambem_e_identica(tmp_path, changed_input, expected):
    source = tmp_path / "revisao/a"
    dest = tmp_path / "revisao/b"
    source.mkdir(parents=True)
    dest.mkdir()
    member = {"case_id": "case", "input": {"pergunta": "O que foi observado?", "relato": "Luz apagada."}}
    group = {"review_id": "same-output-context", "raw": "same answer", "context_ids": ["source:1"], "members": [member]}
    mapping = {"groups": [group]}
    (source / "mapping.json").write_text(json.dumps(mapping))
    decision = {
        "review_id": group["review_id"], "semantic_correct": 1, "hallucination": 0,
        "grounded": 1, "refusal_adequate": 1,
        "reason": "Resposta conferida explicitamente com a observação original.",
    }
    (source / "decisions.jsonl").write_text(json.dumps(decision) + "\n")
    if changed_input:
        member["input"]["relato"] = "Luz acesa."
    (dest / "mapping.json").write_text(json.dumps(mapping))
    result = reuse_exact(tmp_path, "a", "b")
    assert result == (expected, 1)
    records = (dest / "decisions.jsonl").read_text().splitlines()
    assert len(records) == expected
