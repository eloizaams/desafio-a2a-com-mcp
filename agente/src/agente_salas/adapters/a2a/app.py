"""Montagem do app A2A do agente."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from mcp.server.mcpserver import MCPServer
from starlette.applications import Starlette

from agente_salas.adapters.a2a.card import criar_agent_card
from agente_salas.adapters.a2a.contexto import ContextoComVersaoPadrao
from agente_salas.adapters.a2a.executor import ExecutorReservaDeSala
from agente_salas.adapters.mcp_client.cliente import ClienteSalas
from agente_salas.application.pendencias import Pendencias
from agente_salas.application.ponte import Ponte
from agente_salas.constantes import CAMINHO_A2A
from agente_salas.infra.config import ConfigAgente


def criar_app(config: ConfigAgente, servidor_mcp: MCPServer | str | None = None) -> Starlette:
    """Monta o app A2A.

    `servidor_mcp` troca o alvo do `ClienteSalas` (testes); padrão é `config.mcp_url`.
    """
    card = criar_agent_card(config)
    cliente_mcp = ClienteSalas(servidor_mcp or config.mcp_url)
    ponte = Ponte(cliente_mcp, Pendencias())
    handler = DefaultRequestHandler(
        agent_executor=ExecutorReservaDeSala(ponte),
        task_store=InMemoryTaskStore(),
        agent_card=card,
    )
    rotas = create_agent_card_routes(card) + create_jsonrpc_routes(
        handler, CAMINHO_A2A, context_builder=ContextoComVersaoPadrao()
    )

    @asynccontextmanager
    async def ciclo_de_vida(_app: Starlette) -> AsyncIterator[None]:
        async with cliente_mcp:
            yield

    return Starlette(routes=rotas, lifespan=ciclo_de_vida)
