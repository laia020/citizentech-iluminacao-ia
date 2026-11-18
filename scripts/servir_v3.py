"""Inicia explicitamente a API v3 somente neste Mac, sem downloads ou treinamento."""

import argparse
from pathlib import Path

import uvicorn

from citizentech_ia.v3.service import create_reviewed_app


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="experimentos/v3")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    app = create_reviewed_app(Path(args.root))
    try:
        uvicorn.run(app, host="127.0.0.1", port=args.port, workers=1, access_log=False)
    finally:
        app.state.analyzer.close()


if __name__ == "__main__":
    main()
