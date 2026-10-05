"""Modelos puros do domínio: Sala, Reserva, Intervalo."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass(frozen=True)
class Intervalo:
    """Intervalo de tempo semiaberto ``[inicio, fim)``."""

    inicio: datetime
    fim: datetime

    @classmethod
    def a_partir_de_iso(cls, inicio: str, fim: str) -> Intervalo:
        return cls(inicio=datetime.fromisoformat(inicio), fim=datetime.fromisoformat(fim))

    def invertido(self) -> bool:
        return self.fim <= self.inicio

    def duracao(self) -> timedelta:
        return self.fim - self.inicio

    def sobrepoe(self, outro: Intervalo) -> bool:
        return self.inicio < outro.fim and outro.inicio < self.fim


@dataclass(frozen=True)
class Sala:
    id: str
    nome: str
    capacidade: int
    recursos: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Reserva:
    """Reserva com o intervalo mantido como as strings ISO-8601 originais."""

    id: str
    sala: str
    inicio: str
    fim: str
    responsavel: str

    @property
    def intervalo(self) -> Intervalo:
        return Intervalo.a_partir_de_iso(self.inicio, self.fim)
