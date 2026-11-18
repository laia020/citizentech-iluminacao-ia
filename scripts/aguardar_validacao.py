"""Acompanha um treino local conhecido e depois executa somente sua validação."""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from citizentech_ia.v3.analysis_sets import summarize

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--candidate", required=True)
    args = parser.parse_args()
    started = time.monotonic()
    while True:
        process = subprocess.run(
            ["/bin/ps", "-p", str(args.pid), "-o", "command="], capture_output=True, text=True, check=False
        )
        if process.returncode != 0 or f"--name {args.candidate}" not in process.stdout:
            break
        if time.monotonic() - started > 14400:
            raise RuntimeError("Treino não encerrou dentro da janela de acompanhamento.")
        time.sleep(10)
    summary = ROOT / "experimentos/v3/adapters" / args.candidate / "summary.json"
    if not summary.exists() or json.loads(summary.read_text())["microsteps"] != 800:
        raise RuntimeError("Treino não concluiu; validação não iniciada.")
    with (ROOT / f"experimentos/v3/runs/valid-{args.candidate}.log").open("x") as log:
        subprocess.run(
            [
                sys.executable,
                "scripts/experimento_v3.py",
                "evaluate",
                "--name",
                f"valid-{args.candidate}",
                "--mode",
                "rag_finetuning",
                "--adapter",
                f"adapters/{args.candidate}",
                "--split",
                "valid",
            ],
            cwd=ROOT,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
        )
    summarize(ROOT / "experimentos/v3", f"valid-{args.candidate}")
    print("VALIDAÇÃO CONCLUÍDA; seleção e teste continuam pendentes.", flush=True)


if __name__ == "__main__":
    main()
