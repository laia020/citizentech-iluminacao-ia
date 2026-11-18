from ..inference import MLXGenerator
from ..v3.inference import SYSTEM
from ..v3.inference import ReviewedAnalyzer as Analyzer

__all__ = ["SYSTEM", "Analyzer", "Generator"]


class Generator(MLXGenerator):
    def metadata(self):
        result = super().metadata()
        result["modelo"] = self.manifest["model"]
        return result
