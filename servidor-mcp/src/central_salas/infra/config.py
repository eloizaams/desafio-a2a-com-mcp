"""Configuração do servidor MCP lida do ambiente."""

from collections.abc import Mapping
from dataclasses import dataclass

from central_salas.constantes import (
    COMANDO_GERAR_SEGREDO,
    ENV_PORTA,
    ENV_SEGREDO,
    PORTA_PADRAO,
    TAMANHO_MINIMO_SEGREDO_BYTES,
)


class ErroConfig(ValueError):
    """Ambiente inválido para subir o servidor."""


@dataclass(frozen=True)
class ConfigServidor:
    porta: int
    segredo_request_state: str


def carregar_config(ambiente: Mapping[str, str]) -> ConfigServidor:
    return ConfigServidor(
        porta=_ler_porta(ambiente),
        segredo_request_state=_ler_segredo(ambiente),
    )


def _ler_porta(ambiente: Mapping[str, str]) -> int:
    valor = ambiente.get(ENV_PORTA)
    if valor is None:
        return PORTA_PADRAO
    if not valor.isdigit():
        raise ErroConfig(f"{ENV_PORTA} deve ser um número inteiro, recebido: {valor!r}")
    return int(valor)


def _ler_segredo(ambiente: Mapping[str, str]) -> str:
    segredo = ambiente.get(ENV_SEGREDO)
    if not segredo:
        raise ErroConfig(f"{ENV_SEGREDO} é obrigatória (gere com: {COMANDO_GERAR_SEGREDO})")
    if len(segredo.encode()) < TAMANHO_MINIMO_SEGREDO_BYTES:
        raise ErroConfig(f"{ENV_SEGREDO} deve ter pelo menos {TAMANHO_MINIMO_SEGREDO_BYTES} bytes")
    return segredo
