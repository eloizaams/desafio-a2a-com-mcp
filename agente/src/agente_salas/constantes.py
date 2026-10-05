"""Fonte única de nomes, valores padrão e contratos do agente."""

from typing import Final

NOME_AGENTE: Final = "Central de Salas"
VERSAO_AGENTE: Final = "1.0.0"

HOST: Final = "127.0.0.1"
CAMINHO_A2A: Final = "/a2a"

ENV_PORTA: Final = "AGENTE_PORT"
ENV_MCP_URL: Final = "MCP_URL"
PORTA_PADRAO: Final = 7300
MCP_URL_PADRAO: Final = "http://127.0.0.1:7301/mcp"
