"""Casos de uso: listar salas, consultar disponibilidade, reservar (caminho livre).

Conflito em `reservar_sala` é tratado como erro provisório nesta fase; a
fase 002-mrtr troca por `input_required` (ver `ErroConflito`).
"""

from __future__ import annotations

from dataclasses import dataclass

from central_salas.domain.erros import ErroConflito
from central_salas.domain.modelos import Intervalo, Reserva, Sala
from central_salas.domain.politica import conflitos, validar_pedido
from central_salas.infra.repositorio import RepositorioEmMemoria


@dataclass(frozen=True)
class ResultadoDisponibilidade:
    sala: str
    livre: bool
    conflitos: list[Reserva]


@dataclass(frozen=True)
class ResultadoReserva:
    reserva: str
    sala: str
    inicio: str
    fim: str
    responsavel: str


def listar_salas(repositorio: RepositorioEmMemoria) -> list[Sala]:
    return repositorio.listar_salas()


def consultar_disponibilidade(
    repositorio: RepositorioEmMemoria, sala: str, inicio: str, fim: str
) -> ResultadoDisponibilidade:
    intervalo = Intervalo.a_partir_de_iso(inicio, fim)
    if erro := validar_pedido(repositorio.listar_salas(), sala, intervalo):
        raise erro
    encontrados = conflitos(repositorio.listar_reservas(), sala, intervalo)
    return ResultadoDisponibilidade(sala=sala, livre=not encontrados, conflitos=encontrados)


def reservar_sala(
    repositorio: RepositorioEmMemoria, sala: str, inicio: str, fim: str, responsavel: str
) -> ResultadoReserva:
    intervalo = Intervalo.a_partir_de_iso(inicio, fim)
    if erro := validar_pedido(repositorio.listar_salas(), sala, intervalo):
        raise erro
    if conflitos(repositorio.listar_reservas(), sala, intervalo):
        raise ErroConflito
    nova = Reserva(
        id=repositorio.proxima_id(), sala=sala, inicio=inicio, fim=fim, responsavel=responsavel
    )
    repositorio.adicionar_reserva(nova)
    return ResultadoReserva(
        reserva=nova.id, sala=sala, inicio=inicio, fim=fim, responsavel=responsavel
    )
