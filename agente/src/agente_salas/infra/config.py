"""Configuração do agente lida do ambiente."""

from collections.abc import Mapping
from dataclasses import dataclass

from agente_salas.constantes import ENV_MCP_URL, ENV_PORTA, MCP_URL_PADRAO, PORTA_PADRAO


class ErroConfig(ValueError):
    """Ambiente inválido para subir o agente."""


@dataclass(frozen=True)
class ConfigAgente:
    porta: int
    mcp_url: str


def carregar_config(ambiente: Mapping[str, str]) -> ConfigAgente:
    return ConfigAgente(
        porta=_ler_porta(ambiente),
        mcp_url=ambiente.get(ENV_MCP_URL, MCP_URL_PADRAO),
    )


def _ler_porta(ambiente: Mapping[str, str]) -> int:
    valor = ambiente.get(ENV_PORTA)
    if valor is None:
        return PORTA_PADRAO
    if not valor.isdigit():
        raise ErroConfig(f"{ENV_PORTA} deve ser um número inteiro, recebido: {valor!r}")
    return int(valor)
