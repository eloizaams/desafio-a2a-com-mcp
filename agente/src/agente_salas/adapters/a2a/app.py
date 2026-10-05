"""Montagem do app A2A do agente."""

from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from mcp.server.mcpserver import MCPServer
from starlette.applications import Starlette

from agente_salas.adapters.a2a.card import criar_agent_card
from agente_salas.adapters.a2a.contexto import ContextoComVersaoPadrao
from agente_salas.adapters.a2a.executor import ExecutorReservaDeSala
from agente_salas.constantes import CAMINHO_A2A
from agente_salas.infra.config import ConfigAgente


def criar_app(config: ConfigAgente, servidor_mcp: MCPServer | str | None = None) -> Starlette:
    """Monta o app A2A.

    `servidor_mcp` troca o alvo do `ClienteSalas` (testes); padrão é `config.mcp_url`.
    """
    card = criar_agent_card(config)
    handler = DefaultRequestHandler(
        agent_executor=ExecutorReservaDeSala(servidor_mcp or config.mcp_url),
        task_store=InMemoryTaskStore(),
        agent_card=card,
    )
    rotas = create_agent_card_routes(card) + create_jsonrpc_routes(
        handler, CAMINHO_A2A, context_builder=ContextoComVersaoPadrao()
    )
    return Starlette(routes=rotas)
