import json
from pathlib import Path

from a2a.server.request_handlers.response_helpers import agent_card_to_dict

from agente_salas.adapters.a2a.card import criar_agent_card
from agente_salas.infra.config import ConfigAgente

RAIZ = Path(__file__).resolve().parents[5]
WIRE_AGENT_CARD = RAIZ / "exemplos" / "wire" / "07-a2a-agent-card.json"


def test_agent_card_bate_com_o_wire_de_referencia() -> None:
    esperado = json.loads(WIRE_AGENT_CARD.read_text())["response"]["body"]

    config = ConfigAgente(porta=7300, mcp_url="http://127.0.0.1:7301/mcp")
    card = agent_card_to_dict(criar_agent_card(config))

    assert card == esperado
