"""Casos de uso: listar salas, consultar disponibilidade, reservar (com MRTR).

`reservar_sala` separa consulta e gravação (fase 002-mrtr, ver ADR-0006): o
resolver MRTR usa `verificar_conflito_reserva` (só leitura, pode reexecutar a
cada rodada) e a tool usa `reservar_sala` (só grava, depois que a disponibilidade
já foi confirmada pelo resolver).
"""

from __future__ import annotations

from dataclasses import dataclass

from central_salas.domain.alternativas import alternativas as calcular_alternativas
from central_salas.domain.modelos import Intervalo, Reserva, Sala
from central_salas.domain.politica import conflitos, validar_pedido
from central_salas.domain.resultado_reserva import Reservada
from central_salas.infra.repositorio import RepositorioEmMemoria


@dataclass(frozen=True)
class ResultadoDisponibilidade:
    sala: str
    livre: bool
    conflitos: list[Reserva]


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


def verificar_conflito_reserva(
    repositorio: RepositorioEmMemoria, sala: str, intervalo: Intervalo
) -> list[str] | None:
    """Consulta pura (sem efeitos): `None` se `sala` está livre no intervalo.

    Se houver conflito, devolve as alternativas (pode ser lista vazia). Levanta
    `ErroDominio` se o pedido violar a política (sala inexistente, janela, etc.).
    """
    if erro := validar_pedido(repositorio.listar_salas(), sala, intervalo):
        raise erro
    encontrados = conflitos(repositorio.listar_reservas(), sala, intervalo)
    if not encontrados:
        return None
    salas_alt = calcular_alternativas(
        salas=repositorio.listar_salas(),
        reservas=repositorio.listar_reservas(),
        sala_pedida=sala,
        intervalo=intervalo,
    )
    return [s.id for s in salas_alt]


def reservar_sala(
    repositorio: RepositorioEmMemoria, sala: str, inicio: str, fim: str, responsavel: str
) -> Reservada:
    """Grava a reserva. Assume que a disponibilidade de `sala` já foi confirmada."""
    nova = Reserva(
        id=repositorio.proxima_id(), sala=sala, inicio=inicio, fim=fim, responsavel=responsavel
    )
    repositorio.adicionar_reserva(nova)
    return Reservada(reserva=nova.id, sala=sala, inicio=inicio, fim=fim, responsavel=responsavel)
