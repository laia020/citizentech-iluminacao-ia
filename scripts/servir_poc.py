"""Impede iniciar por engano a candidata experimental rejeitada."""


def main():
    raise SystemExit(
        "Candidata experimental não aprovada. Use scripts/servir_poc_validada.py para a POC validada."
    )


if __name__ == "__main__":
    main()
