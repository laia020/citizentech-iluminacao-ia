from citizentech_ia.v3.review_metrics import integral_score, metric_bounds


def test_incerto_nao_vira_acerto_nem_some_do_denominador():
    result = metric_bounds([1, None, 0])
    assert result["n"] == 3 and result["uncertain"] == 1
    assert result["lower_rate"] == 1 / 3
    assert result["upper_rate"] == 2 / 3


def test_formato_invalido_falha_integral_sem_inventar_alucinacao():
    decision = {"semantic_correct": 1, "hallucination": 0, "grounded": 1, "refusal_adequate": 1}
    assert integral_score({"schema_valid": False, "valid_json_and_refs": False}, decision) == 0
    assert decision["hallucination"] == 0
    assert (
        integral_score(
            {"schema_valid": True, "valid_json_and_refs": True}, {**decision, "semantic_correct": None}
        )
        is None
    )
