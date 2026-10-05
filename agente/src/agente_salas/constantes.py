"""Fonte única de nomes, valores padrão e contratos do agente."""

from typing import Final

NOME_AGENTE: Final = "Central de Salas"
VERSAO_AGENTE: Final = "1.0.0"
DESCRICAO_AGENTE: Final = "Reserva salas de reuniao da Hill Valley Tech."
PROVEDOR_ORGANIZACAO: Final = "Hill Valley Tech"
PROVEDOR_URL: Final = "https://hillvalley.example"

MODO_TEXTO: Final = "text/plain"

SKILL_RESERVAR_ID: Final = "reservar-sala"
SKILL_RESERVAR_NOME: Final = "Reservar sala"
SKILL_RESERVAR_DESCRICAO: Final = (
    "Reserva uma sala em um intervalo. Se houver conflito, pergunta qual alternativa usar."
)
SKILL_RESERVAR_TAGS: Final = ("salas", "agenda")
SKILL_RESERVAR_EXEMPLO: Final = (
    "reservar sala=sala-garagem inicio=2026-11-03T14:00:00-03:00 "
    "fim=2026-11-03T15:00:00-03:00 responsavel=Marty"
)

HOST: Final = "127.0.0.1"
CAMINHO_A2A: Final = "/a2a"
VERSAO_PROTOCOLO_A2A: Final = "1.0"

MSG_COMANDO_INVALIDO: Final = (
    "Comando invalido. Use: reservar sala=<id> inicio=<iso8601> fim=<iso8601> "
    "responsavel=<nome>, ou escolha=<id da sala> / escolha=recusar"
)

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
