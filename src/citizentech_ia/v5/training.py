"""Treino1.5B com proteção testada, checkpoints a cada100 e validação inicial/final."""

import json
import math
import time
from importlib import metadata
from pathlib import Path

import mlx.core as mx
import mlx.optimizers as optim
from mlx.utils import tree_flatten, tree_map

from ..datasets import read_jsonl, sha, verify_freeze
from ..v3.training_stable import guarded_update
from .inference import SYSTEM


def run_training(root, name, lr=0.0001, microsteps=400, smoke=False):
    import numpy as np
    import psutil
    from mlx import nn
    from mlx_lm import load
    from mlx_lm.tuner.datasets import CacheDataset, ChatDataset
    from mlx_lm.tuner.trainer import default_loss, evaluate, iterate_batches
    from mlx_lm.tuner.utils import linear_to_lora_layers

    root = Path(root).resolve()
    verify_freeze(root, system_prompt=SYSTEM)
    if microsteps % 4:
        raise ValueError("Número de passos deve permitir acumulação completa de quatro lotes.")
    dest = root / "adapters" / name
    dest.mkdir(parents=True, exist_ok=False)
    np.random.seed(42)
    mx.random.seed(42)
    model, tokenizer = load(str(root / json.loads((root / "configs/model.json").read_text())["model_path"]))
    # Quantized integer codes are preserved. Floating parameters/scales are cast only in memory.
    model.update(
        tree_map(
            lambda x: x.astype(mx.float32) if mx.issubdtype(x.dtype, mx.floating) else x, model.parameters()
        )
    )
    model.freeze()
    lora = {"rank": 16, "scale": 2.0, "dropout": 0.05, "keys": ["self_attn.q_proj", "self_attn.v_proj"]}
    linear_to_lora_layers(model, 16, lora)
    mx.eval(model.parameters())
    initial = dict(tree_flatten(model.trainable_parameters()))
    mx.save_safetensors(str(dest / "initial_adapters.safetensors"), initial)
    settings = {
        "fine_tune_type": "lora",
        "num_layers": 16,
        "lora_parameters": lora,
        "learning_rate": lr,
        "iters": microsteps,
        "batch_size": 1,
        "grad_accumulation_steps": 4,
        "mask_prompt": True,
        "max_seq_length": 2048,
        "optimizer": "adamw",
        "weight_decay": 0.01,
        "compute_dtype": "float32",
        "max_grad_norm": 1.0,
        "numpy_seed": 42,
        "mlx_seed": 42,
        "nonfinite_policy": "abort_before_update; no hidden skipped batches",
        "engine": "local_1_5b_fp32_guarded_v1",
        "compiled_step": False,
        "validation": "initial and exact final only; diagnostic loss without gradients",
    }
    (dest / "adapter_config.json").write_text(json.dumps(settings, indent=2))
    train = CacheDataset(ChatDataset(read_jsonl(root / "dados/mlx/train.jsonl"), tokenizer, mask_prompt=True))
    valid_data = read_jsonl(root / "dados/mlx/valid.jsonl")
    valid = CacheDataset(ChatDataset(valid_data[:4] if smoke else valid_data, tokenizer, mask_prompt=True))
    provenance = {
        "settings": settings,
        "smoke": smoke,
        "started_at": time.time(),
        "frozen_manifest_sha": sha(root / "configs/frozen_manifest.json"),
        "training_code_sha": sha(Path(__file__)),
        "versions": {p: metadata.version(p) for p in ["mlx", "mlx-lm", "numpy"]},
        "base_cast": "FP16 base cast to FP32 only in memory; files unchanged",
        "comparison_note": "new1.5B experiment; no historical model metrics reused",
    }
    (dest / "provenance.json").write_text(json.dumps(provenance, indent=2))
    optimizer = optim.AdamW(learning_rate=lr, weight_decay=0.01)
    grad_fn = nn.value_and_grad(model, default_loss)
    started, initial_swap = time.monotonic(), psutil.swap_memory().used
    updates = clipped_updates = 0
    best_loss, best_iteration = float("inf"), None
    (dest / "best").mkdir()

    def event(kind, **values):
        row = {
            "kind": kind,
            "elapsed_s": time.monotonic() - started,
            **values,
            "peak_memory_gb": mx.get_peak_memory() / 1e9,
            "available_gb": psutil.virtual_memory().available / 1e9,
            "swap_growth_gb": (psutil.swap_memory().used - initial_swap) / 1e9,
        }
        with (dest / "metrics.jsonl").open("a") as f:
            f.write(json.dumps(row) + "\n")
        print(json.dumps(row), flush=True)
        if row["peak_memory_gb"] > 56 and row["available_gb"] < 2:
            raise RuntimeError("Pressão de memória excessiva; parada preservando os checkpoints.")

    def validation(iteration):
        nonlocal best_loss, best_iteration
        value = float(evaluate(model, valid, batch_size=1, num_batches=-1, max_seq_length=2048))
        if not math.isfinite(value):
            raise FloatingPointError("Loss de validação não finita.")
        event("validation", iteration=iteration, val_loss=value)
        if iteration and value < best_loss:
            best_loss, best_iteration = value, iteration
            mx.save_safetensors(
                str(dest / "best/adapters.safetensors"), dict(tree_flatten(model.trainable_parameters()))
            )
            (dest / "best/adapter_config.json").write_text(json.dumps(settings, indent=2))
        model.train()
        return value

    iteration = 0
    try:
        validation(0)
        batches = iterate_batches(train, batch_size=1, max_seq_length=2048, loop=True, seed=42)
        accumulated, losses, tokens = None, [], 0
        for iteration in range(1, microsteps + 1):
            batch = next(batches)
            (loss, ntokens), grad = grad_fn(model, *batch)
            mx.eval(loss, grad)
            loss = float(loss.item())
            if not math.isfinite(loss):
                raise FloatingPointError("Loss de treino não finita; atualização não executada.")
            finite = all(bool(mx.all(mx.isfinite(g)).item()) for _, g in tree_flatten(grad))
            if not finite:
                raise FloatingPointError("Gradiente de microbatch não finito; atualização não executada.")
            accumulated = grad if accumulated is None else tree_map(lambda a, b: a + b, accumulated, grad)
            losses.append(loss)
            tokens += int(ntokens.item())
            if iteration % 4 == 0:
                average = tree_map(lambda g: g / 4, accumulated)
                norm = guarded_update(model, optimizer, average)
                updates += 1
                clipped_updates += norm["clipped"]
                accumulated = None
                event("update", iteration=iteration, optimizer_updates=updates, **norm)
            if iteration % (4 if smoke else 20) == 0:
                event(
                    "train", iteration=iteration, train_loss=sum(losses) / len(losses), trained_tokens=tokens
                )
                losses = []
            if iteration % 100 == 0 or iteration == microsteps:
                mx.save_safetensors(
                    str(dest / f"{iteration:07d}_adapters.safetensors"),
                    dict(tree_flatten(model.trainable_parameters())),
                )
            if iteration == microsteps:
                final_loss = validation(iteration)
            mx.clear_cache()
        current = dict(tree_flatten(model.trainable_parameters()))
        changed = any(bool(mx.any(current[k] != initial[k]).item()) for k in initial)
        if not changed or updates != microsteps // 4:
            raise RuntimeError("Treino não satisfez alteração de pesos e cobertura de atualizações.")
        mx.save_safetensors(str(dest / "adapters.safetensors"), current)
        summary = {
            "microsteps": microsteps,
            "optimizer_updates": updates,
            "elapsed_s": time.monotonic() - started,
            "peak_memory_gb": mx.get_peak_memory() / 1e9,
            "adapters_changed": changed,
            "adapter_sha": sha(dest / "adapters.safetensors"),
            "best_validation_loss": best_loss,
            "best_iteration": best_iteration,
            "final_validation_loss": final_loss,
            "clipped_updates": clipped_updates,
            "skipped_updates": 0,
            "compute_dtype": "float32",
            "numpy_seed": 42,
            "mlx_seed": 42,
        }
        (dest / "summary.json").write_text(json.dumps(summary, indent=2))
        print("SUMMARY " + json.dumps(summary), flush=True)
        return summary
    except Exception as exc:
        (dest / "failure.json").write_text(
            json.dumps(
                {
                    "iteration": iteration,
                    "optimizer_updates": updates,
                    "type": type(exc).__name__,
                    "message": str(exc),
                    "eligible_for_selection": False,
                },
                indent=2,
            )
        )
        raise
