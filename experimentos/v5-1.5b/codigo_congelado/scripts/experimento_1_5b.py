"""Operações explícitas; status não treina, não gera e não baixa modelos."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="experimentos/v5-1.5b")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    training = sub.add_parser("train")
    training.add_argument("--name", required=True)
    training.add_argument("--lr", type=float, default=0.0001)
    training.add_argument("--microsteps", type=int, default=400)
    training.add_argument("--smoke", action="store_true")
    training.add_argument("--execute-training", action="store_true")
    evaluation = sub.add_parser("evaluate")
    evaluation.add_argument("--name", required=True)
    evaluation.add_argument(
        "--mode", choices=["base_sem_contexto", "rag_simples", "rag_finetuning"], required=True
    )
    evaluation.add_argument("--adapter")
    evaluation.add_argument("--split", choices=["valid", "test"], default="valid")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    if args.command == "status":
        print(json.dumps({
            "model": json.loads((root / "configs/model.json").read_text())["model"],
            "base_local": (root / "models/qwen-1.5b-fp16/model.safetensors").exists(),
            "selected_adapter": (root / "configs/selected.json").exists(),
            "state": "prepared_only" if not (root / "configs/selected.json").exists() else "selected",
        }, ensure_ascii=False, indent=2))
    elif args.command == "train":
        if not args.execute_training:
            parser.error("Treinamento não iniciado. Exige autorização e --execute-training explícito.")
        from citizentech_ia.v5.training import run_training

        run_training(root, args.name, args.lr, args.microsteps, args.smoke)
    else:
        from citizentech_ia.v5.evaluation import evaluate

        print(json.dumps(evaluate(
            root, args.name, args.mode, root / args.adapter if args.adapter else None, args.split
        ), ensure_ascii=False))


if __name__ == "__main__":
    main()
