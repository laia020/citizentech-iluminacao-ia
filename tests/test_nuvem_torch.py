"""Testa operações do backend alternativo; não treina nem baixa modelos."""

import numpy as np
import pytest

torch = pytest.importorskip("torch")

from citizentech_ia.cloud.torch_backend import PortableLoRALinear, attach_adapter


@pytest.mark.parametrize("dtype", [torch.float32, torch.float16])
def test_lora_matches_unmerged_fp32_delta_cast_before_addition(dtype):
    rng = np.random.default_rng(42)
    base = torch.nn.Linear(4, 3, bias=False, dtype=dtype)
    with torch.no_grad():
        base.weight.zero_()
    a = rng.normal(size=(4, 2)).astype(np.float32)
    b = rng.normal(size=(2, 3)).astype(np.float32)
    layer = PortableLoRALinear(base, a, b, 2)
    x = torch.tensor(rng.normal(size=(2, 4)), dtype=dtype)
    expected = (2 * ((x.float().numpy() @ a) @ b)).astype(np.float16 if dtype == torch.float16 else np.float32)
    np.testing.assert_allclose(layer(x).detach().numpy(), expected, rtol=.001, atol=.001)
    assert layer.lora_a.dtype == torch.float32
    assert layer(x).dtype == dtype


def test_adapter_rejects_incompatible_shape_without_mutating_base():
    base = torch.nn.Linear(4, 3)
    with pytest.raises(ValueError):
        PortableLoRALinear(base, np.ones((5, 2), np.float32), np.ones((2, 3), np.float32), 2)


def test_adapter_applies_to_qwen_attention_and_never_reapplies():
    from transformers import Qwen2Config, Qwen2ForCausalLM

    model = Qwen2ForCausalLM(Qwen2Config(vocab_size=32, hidden_size=8, intermediate_size=16,
                                       num_hidden_layers=2, num_attention_heads=2, num_key_value_heads=1))
    prefix = "model.layers.1.self_attn.q_proj"
    weights = {prefix + ".lora_a": np.ones((8, 2), np.float32),
               prefix + ".lora_b": np.ones((2, 8), np.float32)}
    assert attach_adapter(model, weights, 2) == 1
    assert isinstance(model.model.layers[1].self_attn.q_proj, PortableLoRALinear)
    with pytest.raises(TypeError):
        attach_adapter(model, weights, 2)
