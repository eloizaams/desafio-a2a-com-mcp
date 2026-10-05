import pytest

from central_salas.application.casos_de_uso import (
    consultar_disponibilidade,
    listar_salas,
    reservar_sala,
)
from central_salas.domain.erros import ErroConflito, ErroSalaInexistente
from central_salas.domain.modelos import Reserva, Sala
from central_salas.infra.repositorio import RepositorioEmMemoria

SALAS = [
    Sala(id="sala-aquario", nome="Aquario", capacidade=4, recursos=["tv"]),
    Sala(id="sala-garagem", nome="Garagem", capacidade=12, recursos=["tv", "quadro"]),
]
RESERVA_GARAGEM = Reserva(
    id="res-0001",
    sala="sala-garagem",
    inicio="2026-11-03T14:00:00-03:00",
    fim="2026-11-03T15:00:00-03:00",
    responsavel="Marty",
)


def _repositorio() -> RepositorioEmMemoria:
    return RepositorioEmMemoria(salas=SALAS, reservas=[RESERVA_GARAGEM])


def test_listar_salas_devolve_as_salas_do_repositorio() -> None:
    assert listar_salas(_repositorio()) == SALAS


def test_consultar_disponibilidade_livre() -> None:
    resultado = consultar_disponibilidade(
        _repositorio(), "sala-aquario", "2026-11-03T09:00:00-03:00", "2026-11-03T10:00:00-03:00"
    )
    assert resultado.sala == "sala-aquario"
    assert resultado.livre is True
    assert resultado.conflitos == []


def test_consultar_disponibilidade_ocupada() -> None:
    resultado = consultar_disponibilidade(
        _repositorio(), "sala-garagem", "2026-11-03T14:30:00-03:00", "2026-11-03T15:30:00-03:00"
    )
    assert resultado.livre is False
    assert [r.id for r in resultado.conflitos] == ["res-0001"]


def test_consultar_disponibilidade_propaga_erro_de_dominio() -> None:
    with pytest.raises(ErroSalaInexistente):
        consultar_disponibilidade(
            _repositorio(),
            "sala-delorean",
            "2026-11-03T09:00:00-03:00",
            "2026-11-03T10:00:00-03:00",
        )


def test_reservar_sala_em_intervalo_livre_cria_reserva_sequencial() -> None:
    repo = _repositorio()
    resultado = reservar_sala(
        repo, "sala-aquario", "2026-11-03T09:00:00-03:00", "2026-11-03T10:00:00-03:00", "Doc"
    )
    assert resultado.reserva == "res-0002"
    assert resultado.sala == "sala-aquario"
    assert resultado.responsavel == "Doc"


def test_reservar_sala_fica_visivel_para_consulta_seguinte_no_mesmo_processo() -> None:
    repo = _repositorio()
    reservar_sala(
        repo, "sala-aquario", "2026-11-03T09:00:00-03:00", "2026-11-03T10:00:00-03:00", "Doc"
    )
    resultado = consultar_disponibilidade(
        repo, "sala-aquario", "2026-11-03T09:00:00-03:00", "2026-11-03T10:00:00-03:00"
    )
    assert resultado.livre is False
    assert [r.id for r in resultado.conflitos] == ["res-0002"]


def test_reservar_sala_propaga_erro_de_dominio() -> None:
    with pytest.raises(ErroSalaInexistente):
        reservar_sala(
            _repositorio(),
            "sala-delorean",
            "2026-11-03T09:00:00-03:00",
            "2026-11-03T10:00:00-03:00",
            "Doc",
        )


def test_reservar_sala_em_conflito_recusa_provisoriamente() -> None:
    repo = _repositorio()
    with pytest.raises(ErroConflito):
        reservar_sala(
            repo, "sala-garagem", "2026-11-03T14:30:00-03:00", "2026-11-03T15:30:00-03:00", "Doc"
        )
    assert repo.listar_reservas() == [RESERVA_GARAGEM]
