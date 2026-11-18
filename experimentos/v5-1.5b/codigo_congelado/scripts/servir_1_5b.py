import argparse
from pathlib import Path

import uvicorn

from citizentech_ia.v5.service import create_model_app


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="experimentos/v5-1.5b")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    app = create_model_app(Path(args.root))
    try:
        uvicorn.run(app, host="127.0.0.1", port=args.port, workers=1, access_log=False)
    finally:
        analyzer = app.state.analyzer
        if analyzer is not None and hasattr(analyzer, "close"):
            analyzer.close()


if __name__ == "__main__":
    main()
