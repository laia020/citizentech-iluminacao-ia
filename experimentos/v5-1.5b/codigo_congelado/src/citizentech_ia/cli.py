import argparse
import json
from pathlib import Path

from .datasets import read_jsonl, validate_splits


def main():
    p = argparse.ArgumentParser(
        description="Etapas explícitas do projeto; nenhuma operação pesada é implícita."
    )
    p.add_argument("--root")
    p.add_argument("--legacy-v2", action="store_true", help="Usa explicitamente a implementação histórica7B.")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("validate-data")
    sub.add_parser("calibrate")
    sub.add_parser("prepare-training")
    tr = sub.add_parser("train")
    tr.add_argument("--name", required=True)
    tr.add_argument("--lr", type=float, required=True)
    tr.add_argument("--microsteps", type=int, default=800)
    tr.add_argument("--smoke", action="store_true")
    ev = sub.add_parser("evaluate")
    ev.add_argument("--name", required=True)
    ev.add_argument("--mode", choices=["base_sem_contexto", "rag_simples", "rag_finetuning"], required=True)
    ev.add_argument("--adapter")
    ev.add_argument("--split", choices=["valid", "test"], default="test")
    ev.add_argument("--limit", type=int)
    sv = sub.add_parser("serve")
    sv.add_argument("--adapter")
    sv.add_argument("--port", type=int, default=8000)
    sub.add_parser("export-openapi")
    rev = sub.add_parser("aggregate-review")
    rev.add_argument("--name", required=True)
    args = p.parse_args()
    project = Path(__file__).resolve().parents[2]
    root = Path(args.root).resolve() if args.root else (
        project if args.legacy_v2 else project / "experimentos/v5-1.5b"
    )
    if not args.legacy_v2 and args.command not in {"validate-data", "serve", "export-openapi"}:
        p.error("Modelo atual1.5B preparado. Use scripts/experimento_1_5b.py para operações explícitas; "
                "comandos históricos exigem --legacy-v2.")
    if args.command == "validate-data":
        rows = [
            r
            for f in ["dados/train.jsonl", "dados/valid.jsonl", "avaliacao/test.jsonl"]
            for r in read_jsonl(root / f)
        ]
        print(json.dumps(validate_splits(rows), ensure_ascii=False))
    elif args.command == "calibrate":
        from .pipeline import calibrate_retrieval

        print(json.dumps(calibrate_retrieval(root), ensure_ascii=False))
    elif args.command == "prepare-training":
        from .training import prepare_training

        print(json.dumps(prepare_training(root)))
    elif args.command == "train":
        from .training import run_training

        run_training(root, args.name, args.lr, args.microsteps, args.smoke)
    elif args.command == "evaluate":
        from .evaluation import evaluate_run

        evaluate_run(
            root, args.name, args.mode, root / args.adapter if args.adapter else None, args.split, args.limit
        )
    elif args.command == "serve":
        import uvicorn

        if args.legacy_v2:
            from .api import create_app
            from .service import local_service

            app = create_app(local_service(root, args.adapter or "adapters/selected/best"))
        else:
            if args.adapter:
                p.error("O serviço1.5B usa somente o adaptador selecionado registrado no experimento.")
            from .v5.service import create_model_app

            app = create_model_app(root)
        try:
            uvicorn.run(app, host="127.0.0.1", port=args.port, workers=1, access_log=False)
        finally:
            analyzer = app.state.analyzer
            if analyzer is not None and hasattr(analyzer, "close"):
                analyzer.close()
    elif args.command == "aggregate-review":
        from .evaluation import aggregate_review

        print(json.dumps(aggregate_review(root, args.name)))
    elif args.command == "export-openapi":
        from .api import create_app

        (root / "docs/openapi.json").write_text(
            json.dumps(create_app().openapi(), ensure_ascii=False, indent=2)
        )


if __name__ == "__main__":
    main()
