"""Unidade dos helpers de parsing de `cliente.py`, sem precisar de servidor:
casos de erro que o fake em processo não consegue forçar porque o próprio SDK
sempre sela um `requestState` junto da `Elicit` (ADR-0006).
"""

import mcp_types as types
import pytest

from agente_salas.adapters.mcp_client.cliente import ErroRespostaInesperada, _pedido_de_entrada


def _input_required(request_state: str | None) -> types.InputRequiredResult:
    pedido = types.ElicitRequest(
        params=types.ElicitRequestFormParams(
            message="escolha uma sala",
            requested_schema={"properties": {"sala": {"enum": ["sala-fusca", "sala-mirante"]}}},
        )
    )
    return types.InputRequiredResult(
        input_requests={"__main__:escolha_de_sala": pedido}, request_state=request_state
    )


def test_pedido_de_entrada_sem_request_state_falha() -> None:
    with pytest.raises(ErroRespostaInesperada, match="requestState"):
        _pedido_de_entrada(_input_required(request_state=None))


def test_pedido_de_entrada_com_request_state_preenche_pendencia() -> None:
    resultado = _pedido_de_entrada(_input_required(request_state="selado"))
    assert resultado.pendencia.request_state == "selado"
    assert resultado.pendencia.campo == "sala"
    assert resultado.pendencia.alternativas == ("sala-fusca", "sala-mirante")
