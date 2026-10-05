"""Resultados possíveis de um pedido de reserva via `ClienteSalas` — puro, sem I/O."""

from __future__ import annotations

from dataclasses import dataclass

from agente_salas.domain.pendencia import PendenciaMRTR


@dataclass(frozen=True)
class Concluido:
    reserva: str
    sala: str
    inicio: str
    fim: str
    responsavel: str
    politica: str | None


@dataclass(frozen=True)
class Recusado:
    motivo: str


@dataclass(frozen=True)
class Falhou:
    mensagem: str


@dataclass(frozen=True)
class PrecisaEntrada:
    pendencia: PendenciaMRTR
    mensagem: str
