import mlx.core as mx
import mlx.optimizers as optim
import pytest
from mlx import nn

from citizentech_ia.v3.training_stable import guarded_update


def test_gradiente_finito_grande_e_limitado_antes_da_atualizacao():
    model = nn.Linear(1, 1, bias=False)
    model.weight = mx.array([[0.0]])
    optimizer = optim.SGD(learning_rate=1.0)
    event = guarded_update(model, optimizer, {"weight": mx.array([[100.0]])}, max_norm=1.0)
    assert float(model.weight.item()) == pytest.approx(-1.0, abs=1e-5)
    assert event["original_norm"] == pytest.approx(100.0)
    assert event["clipped"] is True


@pytest.mark.parametrize("bad", [float("nan"), float("inf")])
def test_gradiente_invalido_interrompe_sem_alterar_pesos_ou_otimizador(bad):
    model = nn.Linear(1, 1, bias=False)
    model.weight = mx.array([[3.0]])
    optimizer = optim.SGD(learning_rate=1.0)
    optimizer.init(model.trainable_parameters())
    before = float(optimizer.state["step"].item())
    with pytest.raises(FloatingPointError):
        guarded_update(model, optimizer, {"weight": mx.array([[bad]])}, max_norm=1.0)
    assert float(model.weight.item()) == 3.0
    assert float(optimizer.state["step"].item()) == before
