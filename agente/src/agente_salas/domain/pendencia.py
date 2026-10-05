"""Pedido de reserva e pendência de escolha (MRTR) — puro, sem I/O."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ArgsReserva:
    sala: str
    inicio: str
    fim: str
    responsavel: str


@dataclass(frozen=True)
class PendenciaMRTR:
    """O que o agente guarda para retomar um `reservar_sala` pausado por `input_required`.

    `request_state` é opaco (HOST-08): guardado e ecoado, nunca aberto.
    """

    chave: str
    campo: str
    alternativas: tuple[str, ...]
    request_state: str


@dataclass(frozen=True)
class RespostaElicitation:
    """Resposta do usuário a uma `PendenciaMRTR`."""

    acao: Literal["accept", "decline", "cancel"]
    sala: str | None = None
