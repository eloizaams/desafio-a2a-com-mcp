"""Política de uso: validação do pedido e busca de conflitos.

Ordem de validação (PLANO.md §3): sala → intervalo invertido → janela → duração.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import time, timedelta, timezone

from central_salas.constantes import (
    DURACAO_MAXIMA_HORAS,
    FUSO_POLITICA_HORAS,
    JANELA_HORA_FIM,
    JANELA_HORA_INICIO,
)
from central_salas.domain.erros import (
    ErroDominio,
    ErroDuracao,
    ErroIntervaloInvertido,
    ErroJanela,
    ErroSalaInexistente,
)
from central_salas.domain.modelos import Intervalo, Reserva, Sala

_FUSO_POLITICA = timezone(timedelta(hours=FUSO_POLITICA_HORAS))
_DURACAO_MAXIMA = timedelta(hours=DURACAO_MAXIMA_HORAS)
_JANELA_INICIO = time(JANELA_HORA_INICIO, 0)
_JANELA_FIM = time(JANELA_HORA_FIM, 0)


def validar_pedido(salas: Sequence[Sala], sala_id: str, intervalo: Intervalo) -> ErroDominio | None:
    if not any(sala.id == sala_id for sala in salas):
        return ErroSalaInexistente(sala_id)
    if intervalo.invertido():
        return ErroIntervaloInvertido()
    if not _dentro_da_janela(intervalo):
        return ErroJanela()
    if intervalo.duracao() > _DURACAO_MAXIMA:
        return ErroDuracao()
    return None


def conflitos(reservas: Sequence[Reserva], sala_id: str, intervalo: Intervalo) -> list[Reserva]:
    return [
        reserva
        for reserva in reservas
        if reserva.sala == sala_id and reserva.intervalo.sobrepoe(intervalo)
    ]


def _dentro_da_janela(intervalo: Intervalo) -> bool:
    inicio_local = intervalo.inicio.astimezone(_FUSO_POLITICA).time()
    fim_local = intervalo.fim.astimezone(_FUSO_POLITICA).time()
    return inicio_local >= _JANELA_INICIO and fim_local <= _JANELA_FIM
