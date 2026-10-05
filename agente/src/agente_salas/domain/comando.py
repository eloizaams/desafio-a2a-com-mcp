"""Parser do formato fixo de comando A2A — puro, sem validar regras de sala."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

PALAVRA_RESERVAR: Final = "reservar"
CHAVE_ESCOLHA: Final = "escolha"
RECUSAR: Final = "recusar"

_CAMPOS_PEDIDO: Final = frozenset({"sala", "inicio", "fim", "responsavel"})


class ErroComando(Exception):
    """Texto que não bate com o formato fixo de pedido ou de escolha."""


@dataclass(frozen=True)
class PedidoReserva:
    sala: str
    inicio: str
    fim: str
    responsavel: str


@dataclass(frozen=True)
class Escolha:
    valor: str  # id de sala, ou RECUSAR


def parse(texto: str) -> PedidoReserva | Escolha:
    tokens = texto.strip().split()
    if tokens and tokens[0] == PALAVRA_RESERVAR:
        return _parse_pedido(tokens[1:])
    if len(tokens) == 1 and tokens[0].startswith(f"{CHAVE_ESCOLHA}="):
        return _parse_escolha(tokens[0])
    raise ErroComando(texto)


def _parse_pedido(tokens: list[str]) -> PedidoReserva:
    campos = _campos(tokens)
    if campos.keys() != _CAMPOS_PEDIDO:
        raise ErroComando(" ".join(tokens))
    return PedidoReserva(
        sala=campos["sala"],
        inicio=campos["inicio"],
        fim=campos["fim"],
        responsavel=campos["responsavel"],
    )


def _parse_escolha(token: str) -> Escolha:
    _, _, valor = token.partition("=")
    if not valor:
        raise ErroComando(token)
    return Escolha(valor=valor)


def _campos(tokens: list[str]) -> dict[str, str]:
    campos: dict[str, str] = {}
    for token in tokens:
        chave, igual, valor = token.partition("=")
        if not igual or not chave or not valor or chave in campos:
            raise ErroComando(token)
        campos[chave] = valor
    return campos
