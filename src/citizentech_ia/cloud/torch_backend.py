"""Backend PyTorch para os pesos MLX originais, com a mesma ordem de operações LoRA."""

import json
import logging
from pathlib import Path

import torch
from torch import nn

from ..datasets import verify_freeze
from ..inference import InvalidGeneration
from ..v5.inference import SYSTEM, Analyzer
from ..v5.pipeline import retriever
from .weights import load_adapter

logger = logging.getLogger("citizentech.cloud.inference")


class PortableLoRALinear(nn.Module):
    def __init__(self, linear, a, b, scale):
        super().__init__()
        if a.shape[0] != linear.in_features or b.shape[1] != linear.out_features:
            raise ValueError("Dimensões LoRA incompatíveis com a base.")
        self.linear = linear
        self.scale = float(scale)
        self.register_buffer("lora_a", torch.from_numpy(a.copy()))
        self.register_buffer("lora_b", torch.from_numpy(b.copy()))

    def forward(self, x):
        # MLX: base(x) + (scale * ((x @ a) @ b)).astype(x.dtype).
        # Keep adapter F32 and cast the delta before addition; do not merge into base weights.
        y = self.linear(x)
        z = (x.to(self.lora_a.dtype) @ self.lora_a) @ self.lora_b
        return y + (self.scale * z).to(x.dtype)


def attach_adapter(model, weights, scale):
    prefixes = sorted({name.rsplit(".", 1)[0] for name in weights})
    replacements = []
    for prefix in prefixes:
        parent_name, child = prefix.rsplit(".", 1)
        parent = model.get_submodule(parent_name)
        linear = getattr(parent, child)
        if not isinstance(linear, nn.Linear):
            raise TypeError("Base já alterada ou módulo incompatível.")
        layer = PortableLoRALinear(linear, weights[prefix + ".lora_a"],
                                  weights[prefix + ".lora_b"], scale)
        replacements.append((parent, child, layer))
    for parent, child, layer in replacements:
        setattr(parent, child, layer)
    return len(replacements)


class TorchGenerator:
    def __init__(self, root, device="cuda", local_model=None):
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.ready = False
        root = Path(root)
        verify_freeze(root / "experimentos/v5-1.5b", system_prompt=SYSTEM)
        weights, adapter_config, self.manifest = load_adapter(root)
        location = self.manifest["model"]
        args = {"revision": self.manifest["revision"], "token": False, "trust_remote_code": False}
        if local_model is not None:
            location = str(Path(local_model).resolve())
            source = json.loads((Path(location) / ".download_source.json").read_text())
            if any(source[k] != self.manifest[k] for k in ["model", "revision"]):
                raise ValueError("Base local sem procedência correspondente.")
            args = {"local_files_only": True, "trust_remote_code": False}
        self.tokenizer = AutoTokenizer.from_pretrained(location, **args)
        self.model = AutoModelForCausalLM.from_pretrained(
            location, dtype=torch.float32,
            attn_implementation="eager", **args,
        )
        count = attach_adapter(self.model, weights, adapter_config["lora_parameters"]["scale"])
        if count != adapter_config["num_layers"] * len(adapter_config["lora_parameters"]["keys"]):
            raise ValueError("Quantidade de módulos alterados diverge da configuração.")
        self.model.requires_grad_(False)
        torch.set_float32_matmul_precision("highest")
        self.model.eval().to(device)
        self.device = device
        self.ready = True

    def count_messages(self, messages):
        return len(self.tokenizer.apply_chat_template(
            messages, tokenize=True, add_generation_prompt=True, return_dict=False))

    def generate(self, messages, max_tokens):
        inputs = self.tokenizer.apply_chat_template(
            messages, tokenize=True, add_generation_prompt=True, return_tensors="pt", return_dict=True)
        inputs = inputs.to(self.device)
        with torch.inference_mode():
            output = self.model.generate(**inputs, max_new_tokens=max_tokens, do_sample=False,
                                         pad_token_id=self.tokenizer.eos_token_id)
        return self.tokenizer.decode(output[0, inputs["input_ids"].shape[-1]:], skip_special_tokens=True)

    def metadata(self):
        return {"modelo": self.manifest["model"], "revisao_modelo": self.manifest["revision"],
                "adaptador": "r1-sha256:" + self.manifest["adapter_sha"]}


class CloudAnalyzer(Analyzer):
    def parse(self, raw, chunks, occurrence):
        try:
            return super().parse(raw, chunks, occurrence)
        except InvalidGeneration as error:
            logger.warning("Saída inválida: chars=%s causa=%s", len(raw), type(error.__cause__).__name__)
            raise


def create_analyzer(root, device="cuda", local_model=None):
    root = Path(root)
    generator = TorchGenerator(root, device=device, local_model=local_model)
    threshold = json.loads((root / "experimentos/v5-1.5b/configs/retrieval.json").read_text())["threshold"]
    return CloudAnalyzer(generator, retriever(root / "experimentos/v5-1.5b"), threshold=threshold)
