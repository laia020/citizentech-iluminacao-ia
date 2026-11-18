"""Inicializador exclusivo do Space; não inicia hospedagem no Mac do usuário."""

import os
import sys
from pathlib import Path


def report_startup(zero):
    startup = getattr(zero, "startup", None)
    if not callable(startup):
        raise RuntimeError("A hospedagem exige ZeroGPU ativo; não há fallback para outra máquina.")  # noqa: TRY004
    # mount_gradio_app does not call Blocks.launch, where spaces installs this hook.
    # Report normally after registering GPU handlers and packing the model tensors.
    startup()


def main():
    if not os.environ.get("SPACE_ID"):
        raise SystemExit("Este inicializador é exclusivo da hospedagem Hugging Face Spaces.")
    import spaces
    import uvicorn

    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root / "src"))
    from citizentech_ia.cloud.space_app import build_app
    from citizentech_ia.cloud.torch_backend import create_analyzer

    analyzer = create_analyzer(root, device="cuda")
    app = build_app(root, analyzer, gpu_decorator=spaces.GPU, port=7860)
    report_startup(spaces.zero)
    uvicorn.run(app, host="0.0.0.0", port=7860, access_log=False)


if __name__ == "__main__":
    main()
