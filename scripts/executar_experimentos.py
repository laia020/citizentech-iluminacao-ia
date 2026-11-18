"""Execução sequencial e local. Não publica, não suspende e não oculta falhas."""

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
STATUS = ROOT / "runs/progress.json"
started = time.time()


def stage(name, args):
    STATUS.write_text(
        json.dumps({"stage": name, "state": "running", "started": started, "updated": time.time()}, indent=2)
    )
    print("STAGE " + name, flush=True)
    with (ROOT / "runs" / f"{name}.log").open("x") as log:
        process = subprocess.run(
            [sys.executable, "-m", "citizentech_ia.cli", *args],
            stdout=log,
            stderr=subprocess.STDOUT,
            check=False,
        )
    if process.returncode:
        STATUS.write_text(
            json.dumps(
                {"stage": name, "state": "failed", "returncode": process.returncode, "updated": time.time()},
                indent=2,
            )
        )
        raise SystemExit(f"Falha em {name}; ver runs/{name}.log; artefatos preservados.")


stage("treino-lr1e5", ["train", "--name", "lr1e5", "--lr", "0.00001"])
stage("treino-lr5e5", ["train", "--name", "lr5e5", "--lr", "0.00005"])
for name in ["lr1e5", "lr5e5"]:
    stage(
        "valid-" + name,
        [
            "evaluate",
            "--name",
            "valid-" + name,
            "--mode",
            "rag_finetuning",
            "--adapter",
            f"adapters/{name}/best",
            "--split",
            "valid",
        ],
    )

candidates = {
    name: json.loads((ROOT / f"runs/valid-{name}/metrics.json").read_text()) for name in ["lr1e5", "lr5e5"]
}
# Technical selection proxy; independent human correctness/fidelity review remains pending.
selected = max(
    candidates,
    key=lambda n: (
        candidates[n]["status_match_rate"],
        candidates[n]["valid_json_and_refs_rate"],
        -candidates[n]["median_seconds"],
    ),
)
dest = ROOT / "adapters/selected/best"
dest.parent.mkdir(exist_ok=False)
shutil.copytree(ROOT / f"adapters/{selected}/best", dest)
(ROOT / "configs/selected.json").write_text(
    json.dumps(
        {
            "candidate": selected,
            "adapter": "adapters/selected/best",
            "criteria": "status_match, schema_and_refs, median_latency on validation only; technical proxy, not human semantic accuracy",
            "human_review": "pending",
            "validation_candidates": candidates,
        },
        ensure_ascii=False,
        indent=2,
    )
)
for name, mode, adapter in [
    ("final-A", "base_sem_contexto", None),
    ("final-B", "rag_simples", None),
    ("final-C", "rag_finetuning", "adapters/selected/best"),
]:
    args = ["evaluate", "--name", name, "--mode", mode]
    if adapter:
        args += ["--adapter", adapter]
    stage(name, args)
from citizentech_ia.evaluation import publish_comparison

publish_comparison(ROOT, ["final-A", "final-B", "final-C"])
STATUS.write_text(
    json.dumps(
        {
            "stage": "experimentos_concluidos",
            "state": "complete",
            "selected": selected,
            "elapsed_s": time.time() - started,
            "updated": time.time(),
        },
        indent=2,
    )
)
print("EXPERIMENTOS CONCLUÍDOS " + selected, flush=True)
