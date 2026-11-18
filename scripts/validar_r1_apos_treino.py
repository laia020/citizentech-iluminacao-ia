"""Espera o treino em curso encerrar e gera validação; não seleciona nem abre teste."""

import os
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PID = 9452
started = time.monotonic()
while True:
    try:
        os.kill(PID, 0)
    except ProcessLookupError:
        break
    if time.monotonic() - started > 14400:
        raise RuntimeError("Treino não encerrou dentro da janela de acompanhamento.")
    time.sleep(10)
summary = ROOT / "experimentos/v3/adapters/r1/summary.json"
if not summary.exists():
    raise RuntimeError("Treino encerrou sem resumo de conclusão; validação não iniciada.")
with (ROOT / "experimentos/v3/runs/valid-r1.log").open("x") as log:
    subprocess.run(
        [
            str(ROOT / ".venv/bin/python"),
            "scripts/experimento_v3.py",
            "evaluate",
            "--name",
            "valid-r1",
            "--mode",
            "rag_finetuning",
            "--adapter",
            "adapters/r1",
            "--split",
            "valid",
        ],
        cwd=ROOT,
        stdout=log,
        stderr=subprocess.STDOUT,
        check=True,
    )
from citizentech_ia.v3.analysis_sets import summarize

summarize(ROOT / "experimentos/v3", "valid-r1")
print("VALIDAÇÃO R1 CONCLUÍDA; SELEÇÃO E TESTE CONTINUAM PENDENTES.", flush=True)
