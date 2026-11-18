"""Recarrega os adaptadores do teste técnico e faz geração curta, sem avaliar qualidade."""

import json
from pathlib import Path

from citizentech_ia.inference import MLXGenerator

root = Path(__file__).resolve().parents[1]
g = MLXGenerator(root / "models/qwen-7b-4bit", root / "adapters/smoke-01/best")
raw = g.generate([{"role": "user", "content": "Responda apenas OK."}], max_tokens=4)
if not raw:
    raise SystemExit("Geração vazia após recarga.")
(root / "adapters/smoke-01/reload.json").write_text(
    json.dumps(
        {"reloaded": True, "raw": raw, "model": g.metadata(), "scope": "technical_only"},
        ensure_ascii=False,
        indent=2,
    )
)
print("Recarga técnica validada:", raw)
