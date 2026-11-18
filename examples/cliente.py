"""Cliente real de contrato; não simula inferência e não cria ordem de serviço."""

import argparse
import json
from pathlib import Path

import httpx

parser = argparse.ArgumentParser()
parser.add_argument("--url", default="http://127.0.0.1:8000")
parser.add_argument("--arquivo", default="examples/ocorrencia.json")
a = parser.parse_args()
r = httpx.post(a.url.rstrip("/") + "/v1/analisar", json=json.loads(Path(a.arquivo).read_text()), timeout=180)
print(json.dumps(r.json(), ensure_ascii=False, indent=2))
r.raise_for_status()
