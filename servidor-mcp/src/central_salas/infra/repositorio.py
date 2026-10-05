"""Repositório em memória: salas fixas + reservas mutáveis, visível só no processo."""

from __future__ import annotations

from central_salas.constantes import DIGITOS_ID_RESERVA, PREFIXO_RESERVA
from central_salas.domain.modelos import Reserva, Sala


class RepositorioEmMemoria:
    def __init__(self, salas: list[Sala], reservas: list[Reserva]) -> None:
        self._salas = list(salas)
        self._reservas = list(reservas)

    def listar_salas(self) -> list[Sala]:
        return list(self._salas)

    def listar_reservas(self) -> list[Reserva]:
        return list(self._reservas)

    def adicionar_reserva(self, reserva: Reserva) -> None:
        self._reservas.append(reserva)

    def proxima_id(self) -> str:
        maior = 0
        for reserva in self._reservas:
            if reserva.id.startswith(PREFIXO_RESERVA):
                maior = max(maior, int(reserva.id[len(PREFIXO_RESERVA) :]))
        return f"{PREFIXO_RESERVA}{maior + 1:0{DIGITOS_ID_RESERVA}d}"
