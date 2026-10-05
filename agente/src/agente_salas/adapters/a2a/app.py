"""Montagem do app A2A do agente."""

from a2a.server.routes import create_agent_card_routes
from a2a.types import AgentCard, AgentInterface
from starlette.applications import Starlette

from agente_salas.constantes import CAMINHO_A2A, HOST, NOME_AGENTE, VERSAO_AGENTE
from agente_salas.infra.config import ConfigAgente


def criar_app(config: ConfigAgente) -> Starlette:
    card = AgentCard(
        name=NOME_AGENTE,
        version=VERSAO_AGENTE,
        supported_interfaces=[
            AgentInterface(
                url=f"http://{HOST}:{config.porta}{CAMINHO_A2A}",
                protocol_binding="JSONRPC",
                protocol_version="1.0",
            )
        ],
    )
    return Starlette(routes=create_agent_card_routes(card))
