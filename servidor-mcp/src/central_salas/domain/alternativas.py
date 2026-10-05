"""Sugestão de salas alternativas quando a sala pedida está ocupada.

Regra (PLANO.md §3): salas ≠ pedida, livres no intervalo, capacidade >= pedida,
ordenadas por (capacidade, id), no máximo `MAXIMO_ALTERNATIVAS`.
"""

from __future__ import annotations

from collections.abc import Sequence

from central_salas.constantes import MAXIMO_ALTERNATIVAS
from central_salas.domain.modelos import Intervalo, Reserva, Sala
from central_salas.domain.politica import conflitos


def alternativas(
    salas: Sequence[Sala], reservas: Sequence[Reserva], sala_pedida: str, intervalo: Intervalo
) -> list[Sala]:
    sala_pedida_obj = next(sala for sala in salas if sala.id == sala_pedida)
    candidatas = [
        sala
        for sala in salas
        if sala.id != sala_pedida and sala.capacidade >= sala_pedida_obj.capacidade
    ]
    livres = [sala for sala in candidatas if not conflitos(reservas, sala.id, intervalo)]
    ordenadas = sorted(livres, key=lambda sala: (sala.capacidade, sala.id))
    return ordenadas[:MAXIMO_ALTERNATIVAS]
