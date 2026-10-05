"""Montagem do servidor MCP (Streamable HTTP, stateless)."""

from mcp.server.mcpserver import MCPServer, RequestStateSecurity
from starlette.applications import Starlette

from central_salas.constantes import (
    CAMINHO_MCP,
    NOME_SERVIDOR,
    TTL_REQUEST_STATE_SEGUNDOS,
    VERSAO_SERVIDOR,
)
from central_salas.infra.config import ConfigServidor


def criar_app(config: ConfigServidor) -> Starlette:
    servidor = MCPServer(
        name=NOME_SERVIDOR,
        version=VERSAO_SERVIDOR,
        request_state_security=RequestStateSecurity(
            keys=[config.segredo_request_state],
            ttl=TTL_REQUEST_STATE_SEGUNDOS,
        ),
    )
    return servidor.streamable_http_app(
        streamable_http_path=CAMINHO_MCP,
        stateless_http=True,
        json_response=True,
    )
