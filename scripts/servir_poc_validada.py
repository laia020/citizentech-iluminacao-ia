"""Modelo v5 original com bloqueio explícito de incompatibilidades documentais conhecidas."""

import argparse
from pathlib import Path

import uvicorn

from citizentech_ia.citation_guard import attach_guard
from citizentech_ia.v5.service import create_model_app


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    app = attach_guard(create_model_app(root / "experimentos/v5-1.5b"))
    try:
        uvicorn.run(app, host="127.0.0.1", port=args.port, access_log=False)
    finally:
        analyzer = app.state.analyzer
        if analyzer is not None:
            analyzer.close()


if __name__ == "__main__":
    main()
