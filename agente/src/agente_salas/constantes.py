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

# Cliente MCP (ADR-0003): mesmos nomes de tool/URI do servidor, duplicados aqui
# porque nenhum import cruzado entre `agente/` e `servidor-mcp/` é permitido.
PROTOCOLO_MCP: Final = "2026-07-28"
CLIENTE_MCP_NOME: Final = "agente-central-de-salas"
TOOL_RESERVAR_SALA: Final = "reservar_sala"
URI_POLITICA: Final = "politica://uso"
PREFIXO_VERSAO_POLITICA: Final = "versao:"
