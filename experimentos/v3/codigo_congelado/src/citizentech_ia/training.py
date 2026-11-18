"""Treinamento local auditável; nunca chamado pela API."""

import json
import math
import platform
import shutil
import time
from importlib import metadata
from pathlib import Path
from types import SimpleNamespace

from .datasets import read_jsonl, sha, verify_freeze
from .inference import Analyzer
from .pipeline import load_retriever
from .schemas import Occurrence


def prepare_training(root):
    from transformers import AutoTokenizer

    root = Path(root)
    tokenizer = AutoTokenizer.from_pretrained(str(root / "models/qwen-7b-4bit"), local_files_only=True)

    class Counter:
        def count_messages(self, messages):
            return len(
                tokenizer.apply_chat_template(
                    messages, tokenize=True, add_generation_prompt=True, return_dict=False
                )
            )

    threshold = json.loads((root / "configs/retrieval.json").read_text())["threshold"]
    a = Analyzer(Counter(), load_retriever(root), threshold=threshold)
    chunks = {c["chunk_id"]: c for c in a.retriever.chunks}
    dest = root / "dados/mlx"
    dest.mkdir(exist_ok=False)
    stats = {}
    for split in ["train", "valid"]:
        examples = []
        injected = 0
        lengths = []
        for row in read_jsonl(root / f"dados/{split}.jsonl"):
            occurrence = Occurrence.model_validate(row["input"])
            messages, retrieved, _ = a.prepare(occurrence)
            # Supervised targets use an oracle supporting passage when retrieval missed it.
            # This applies only to training/validation loss; never inject test evidence this way.
            source = row["target"]["fontes"][0]
            if source not in {c["chunk_id"] for c in retrieved}:
                support = chunks[source]
                context = json.loads(messages[1]["content"])
                context["CONTEXTO"] = [{"chunk_id": support["chunk_id"], "texto": support["text"]}] + context[
                    "CONTEXTO"
                ][:2]
                messages[1]["content"] = json.dumps(context, ensure_ascii=False)
                injected += 1
            messages.append({"role": "assistant", "content": json.dumps(row["target"], ensure_ascii=False)})
            length = len(tokenizer.apply_chat_template(messages, tokenize=True, return_dict=False))
            if length > 2048:
                raise ValueError(f"Exemplo excede contexto: {row['case_id']}: {length}")
            lengths.append(length)
            examples.append({"messages": messages})
        with (dest / f"{split}.jsonl").open("x") as f:
            for x in examples:
                f.write(json.dumps(x, ensure_ascii=False) + "\n")
        stats[split] = {
            "n": len(examples),
            "max_tokens": max(lengths),
            "mean_tokens": sum(lengths) / len(lengths),
            "oracle_support_insertions": injected,
            "sha": sha(dest / f"{split}.jsonl"),
        }
    (dest / "manifest.json").write_text(json.dumps(stats, indent=2))
    return stats


def run_training(root, name, lr, microsteps=800, smoke=False, system_prompt=None):
    import mlx.core as mx
    import psutil
    from mlx.utils import tree_flatten
    from mlx_lm import load
    from mlx_lm.lora import CONFIG_DEFAULTS, train_model
    from mlx_lm.tuner.callbacks import TrainingCallback
    from mlx_lm.tuner.datasets import CacheDataset, ChatDataset
    from mlx_lm.tuner.trainer import evaluate

    root = Path(root).resolve()
    verify_freeze(root, system_prompt=system_prompt)
    dest = root / "adapters" / name
    dest.mkdir(parents=True, exist_ok=False)
    model, tokenizer = load(str(root / "models/qwen-7b-4bit"))
    train = ChatDataset(read_jsonl(root / "dados/mlx/train.jsonl"), tokenizer, mask_prompt=True)
    valid = ChatDataset(read_jsonl(root / "dados/mlx/valid.jsonl"), tokenizer, mask_prompt=True)
    # Smoke uses a small validation sample; official candidates use the full 80 examples.
    if smoke:
        valid = ChatDataset(valid._data[:4], tokenizer, mask_prompt=True)
    settings = {
        **CONFIG_DEFAULTS,
        "model": str(root / "models/qwen-7b-4bit"),
        "train": True,
        "fine_tune_type": "lora",
        "optimizer": "adamw",
        "optimizer_config": {"adamw": {"weight_decay": 0.01}},
        "data": str(root / "dados/mlx"),
        "seed": 42,
        "num_layers": 16,
        "batch_size": 1,
        "iters": microsteps,
        "val_batches": -1,
        "learning_rate": lr,
        "steps_per_report": 4 if smoke else 20,
        "steps_per_eval": 100,
        "save_every": 100,
        "max_seq_length": 2048,
        "grad_accumulation_steps": 4,
        "mask_prompt": True,
        "adapter_path": str(dest),
        "lora_parameters": {
            "rank": 16,
            "scale": 2.0,
            "dropout": 0.05,
            "keys": ["self_attn.q_proj", "self_attn.v_proj"],
        },
    }
    args = SimpleNamespace(**settings)
    started = time.time()
    initial_swap = psutil.swap_memory().used
    provenance = {
        "settings": settings,
        "started_at": started,
        "smoke": smoke,
        "python": platform.python_version(),
        "machine": platform.machine(),
        "versions": {p: metadata.version(p) for p in ["mlx", "mlx-lm", "transformers", "numpy"]},
        "dataset_manifest_sha": sha(root / "dados/manifest.json"),
        "frozen_manifest_sha": sha(root / "configs/frozen_manifest.json"),
        "prepared_data_manifest": json.loads((root / "dados/mlx/manifest.json").read_text()),
        "prompt_version": json.loads((root / "configs/frozen_manifest.json").read_text()).get(
            "prompt_version"
        ),
        "model_provenance": json.loads((root / "models/qwen-7b-4bit/provenance.json").read_text()),
    }
    (dest / "provenance.json").write_text(json.dumps(provenance, indent=2))
    metrics_path = dest / "metrics.jsonl"
    best_path = dest / "best"
    best_path.mkdir()

    class Callback(TrainingCallback):
        best = float("inf")
        initial_weights = None
        best_iteration = None

        def event(self, kind, event):
            row = {
                "kind": kind,
                "elapsed_s": time.time() - started,
                **event,
                "rss_gb": psutil.Process().memory_info().rss / 1e9,
                "available_gb": psutil.virtual_memory().available / 1e9,
                "swap_growth_gb": (psutil.swap_memory().used - initial_swap) / 1e9,
            }
            with metrics_path.open("a") as f:
                f.write(json.dumps(row) + "\n")
            print("METRIC " + json.dumps(row), flush=True)

        def on_train_loss_report(self, event):
            if not math.isfinite(event["train_loss"]):
                raise RuntimeError("Loss não finita.")
            if mx.get_peak_memory() > 56e9 and psutil.virtual_memory().available < 2e9:
                raise RuntimeError("Pressão de memória excessiva; treino interrompido preservando artefatos.")
            self.event("train", event)

        def on_val_loss_report(self, event):
            if not math.isfinite(event["val_loss"]):
                raise RuntimeError("Validation loss não finita.")
            self.event("validation", event)
            iteration = event["iteration"]
            weights = dict(tree_flatten(model.trainable_parameters()))
            if self.initial_weights is None:
                mx.save_safetensors(str(dest / "initial_adapters.safetensors"), weights)
                self.initial_weights = True
            if iteration > 0 and event["val_loss"] < self.best:
                self.best = event["val_loss"]
                self.best_iteration = iteration
                mx.save_safetensors(str(best_path / "adapters.safetensors"), weights)
                shutil.copy2(dest / "adapter_config.json", best_path / "adapter_config.json")

    callback = Callback()
    train_model(args, model, train, valid, training_callback=callback)
    # Official trainer validates BEFORE each periodic microstep; evaluate exact final weights as well.
    model.eval()
    loss = evaluate(model, CacheDataset(valid), batch_size=1, num_batches=-1, max_seq_length=2048)
    callback.on_val_loss_report(
        {"iteration": microsteps, "val_loss": float(loss), "val_time": None, "final": True}
    )
    initial = mx.load(str(dest / "initial_adapters.safetensors"))
    current = dict(tree_flatten(model.trainable_parameters()))
    changed = any(bool(mx.any(current[k] != initial[k]).item()) for k in initial)
    if not changed:
        raise RuntimeError("Adaptadores não foram alterados.")
    summary = {
        "microsteps": microsteps,
        "optimizer_updates": microsteps // 4,
        "elapsed_s": time.time() - started,
        "seconds_per_update": (time.time() - started) / (microsteps // 4),
        "peak_memory_gb": mx.get_peak_memory() / 1e9,
        "adapters_changed": changed,
        "best_validation_loss": callback.best,
        "best_iteration": callback.best_iteration,
        "final_validation_loss": float(loss),
        "adapter_sha": sha(dest / "adapters.safetensors"),
    }
    (dest / "summary.json").write_text(json.dumps(summary, indent=2))
    print("SUMMARY " + json.dumps(summary), flush=True)
    return summary
