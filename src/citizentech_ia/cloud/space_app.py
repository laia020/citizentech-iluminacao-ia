"""Aplicação Gradio/ZeroGPU com a tela Akona e o contrato HTTP existentes."""

from pathlib import Path

from .engine import CloudEngine
from .proxy import create_proxy_app


def build_app(root, analyzer, gpu_decorator=None, port=7860):
    import gradio as gr
    from gradio_client import Client

    root = Path(root)
    engine = CloudEngine(analyzer)

    def analyze_gpu(value):
        return engine(value)

    callback = gpu_decorator(analyze_gpu) if gpu_decorator else analyze_gpu
    with gr.Blocks(title="Akona Energy — IA", analytics_enabled=False) as gpu:
        gr.Markdown("# Akona Energy — API de IA\nPOC pública: use somente observações fictícias.")
        occurrence = gr.JSON(label="Ocorrência fictícia")
        answer = gr.JSON(label="Resposta e código HTTP")
        gr.Button("Analisar").click(callback, occurrence, answer, api_name="analisar", concurrency_limit=1)
    gpu.queue(default_concurrency_limit=1, max_size=8, api_open=False)

    def predict(value, headers):
        # Loopback belongs to this cloud instance, never to the user's computer.
        client = Client(f"http://127.0.0.1:{port}/gpu/", token=False, headers=headers,
                        verbose=False, analytics_enabled=False, max_workers=1,
                        httpx_kwargs={"timeout": 180})
        job = None
        try:
            job = client.submit(value, api_name="/analisar")
            return job.result(timeout=180)
        finally:
            if job is not None and not job.done():
                job.cancel()
            client.close()

    page = root / "cloud-demo.html"
    app = create_proxy_app(predict, lambda: analyzer.generator.ready, page)
    return gr.mount_gradio_app(app, gpu, path="/gpu", show_error=False,
                              footer_links=[], enable_monitoring=False, ssr_mode=False)
