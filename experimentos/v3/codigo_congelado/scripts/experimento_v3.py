"""Operações locais explícitas para a revisão; não publica nem suspende o Mac."""

import argparse
import json
from pathlib import Path

from citizentech_ia.training import run_training
from citizentech_ia.v3.evaluation import evaluate
from citizentech_ia.v3.inference import SYSTEM


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", default="experimentos/v3")
    sub = p.add_subparsers(dest="command", required=True)
    tr = sub.add_parser("train")
    tr.add_argument("--name", required=True)
    tr.add_argument("--lr", type=float, default=0.00001)
    tr.add_argument("--microsteps", type=int, default=800)
    tr.add_argument("--smoke", action="store_true")
    ev = sub.add_parser("evaluate")
    ev.add_argument("--name", required=True)
    ev.add_argument("--mode", choices=["base_sem_contexto", "rag_simples", "rag_finetuning"], required=True)
    ev.add_argument("--adapter")
    ev.add_argument("--split", choices=["valid", "test"], default="valid")
    args = p.parse_args()
    root = Path(args.root).resolve()
    if args.command == "train":
        run_training(root, args.name, args.lr, args.microsteps, args.smoke, system_prompt=SYSTEM)
    else:
        print(
            json.dumps(
                evaluate(
                    root, args.name, args.mode, root / args.adapter if args.adapter else None, args.split
                ),
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()
