"""Fonte única de nomes, valores padrão e contratos do servidor MCP."""

from typing import Final

NOME_SERVIDOR: Final = "central-de-salas"
VERSAO_SERVIDOR: Final = "1.0.0"

HOST: Final = "127.0.0.1"
CAMINHO_MCP: Final = "/mcp"

ENV_PORTA: Final = "MCP_PORT"
ENV_SEGREDO: Final = "REQUEST_STATE_SECRET"
PORTA_PADRAO: Final = 7301
TAMANHO_MINIMO_SEGREDO_BYTES: Final = 32
COMANDO_GERAR_SEGREDO: Final = "python3 -c 'import secrets; print(secrets.token_hex(32))'"
TTL_REQUEST_STATE_SEGUNDOS: Final = 10 * 60
