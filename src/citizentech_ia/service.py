"""Mantém criação, uso e liberação do MLX em um único worker do serviço."""

from concurrent.futures import ThreadPoolExecutor


class _Metadata:
    def __init__(self, values):
        self.ready = True
        self.values = values

    def metadata(self):
        return dict(self.values)


class ThreadBoundAnalyzer:
    def __init__(self, factory):
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="citizentech-mlx")
        try:
            self._analyzer = self._executor.submit(factory).result()
            self.mode = self._analyzer.mode
            self.base_version = self._analyzer.base_version
            metadata = self._executor.submit(self._analyzer.generator.metadata).result()
            self.generator = _Metadata(metadata)
        except Exception:
            self._executor.shutdown(wait=True)
            raise

    def analyze(self, occurrence):
        if not self.generator.ready:
            raise RuntimeError("Serviço encerrado.")
        return self._executor.submit(self._analyzer.analyze, occurrence).result()

    def _release(self):
        import gc

        self._analyzer = None
        gc.collect()

    def close(self):
        if self.generator.ready:
            self.generator.ready = False
            self._executor.submit(self._release).result()
            self._executor.shutdown(wait=True)


def local_service(root, adapter):
    def factory():
        import json

        from .inference import Analyzer, MLXGenerator
        from .pipeline import load_retriever

        return Analyzer(
            MLXGenerator(root / "models/qwen-7b-4bit", root / adapter),
            load_retriever(root),
            threshold=json.loads((root / "configs/retrieval.json").read_text())["threshold"],
        )

    return ThreadBoundAnalyzer(factory)
