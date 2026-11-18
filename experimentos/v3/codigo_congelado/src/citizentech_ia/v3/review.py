def review_manifest():
    return {
        "reviewer_kind": "ai_assisted_technical_review",
        "independent_human_review": False,
        "claim": "Resultados técnicos neste benchmark; não certificam generalização ou ausência de alucinação.",
        "dimensions": [
            "status",
            "schema",
            "citation_membership",
            "semantic_correctness",
            "unsupported_claims",
            "refusal_adequacy",
        ],
        "invalid_format_is_not_automatically_hallucination": True,
        "uncertainty": "Classificações semânticas por IA devem receber revisão humana independente.",
    }
