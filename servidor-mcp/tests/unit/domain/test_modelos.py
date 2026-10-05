from datetime import timedelta

from central_salas.domain.modelos import Intervalo, Reserva, Sala


def test_intervalo_parseia_iso8601_com_offset() -> None:
    intervalo = Intervalo.a_partir_de_iso("2026-11-03T09:00:00-03:00", "2026-11-03T10:00:00-03:00")
    assert intervalo.inicio.isoformat() == "2026-11-03T09:00:00-03:00"
    assert intervalo.fim.isoformat() == "2026-11-03T10:00:00-03:00"


def test_intervalo_duracao() -> None:
    intervalo = Intervalo.a_partir_de_iso("2026-11-03T09:00:00-03:00", "2026-11-03T10:30:00-03:00")
    assert intervalo.duracao() == timedelta(hours=1, minutes=30)


def test_intervalo_invertido_quando_fim_antes_do_inicio() -> None:
    intervalo = Intervalo.a_partir_de_iso("2026-11-03T10:00:00-03:00", "2026-11-03T09:00:00-03:00")
    assert intervalo.invertido() is True


def test_intervalo_invertido_quando_fim_igual_ao_inicio() -> None:
    intervalo = Intervalo.a_partir_de_iso("2026-11-03T09:00:00-03:00", "2026-11-03T09:00:00-03:00")
    assert intervalo.invertido() is True


def test_intervalo_nao_invertido_quando_fim_depois_do_inicio() -> None:
    intervalo = Intervalo.a_partir_de_iso("2026-11-03T09:00:00-03:00", "2026-11-03T10:00:00-03:00")
    assert intervalo.invertido() is False


def test_intervalos_sobrepostos_parcialmente() -> None:
    a = Intervalo.a_partir_de_iso("2026-11-03T09:00:00-03:00", "2026-11-03T10:00:00-03:00")
    b = Intervalo.a_partir_de_iso("2026-11-03T09:30:00-03:00", "2026-11-03T11:00:00-03:00")
    assert a.sobrepoe(b) is True
    assert b.sobrepoe(a) is True


def test_intervalos_adjacentes_semiabertos_nao_se_sobrepoem() -> None:
    a = Intervalo.a_partir_de_iso("2026-11-03T09:00:00-03:00", "2026-11-03T10:00:00-03:00")
    b = Intervalo.a_partir_de_iso("2026-11-03T10:00:00-03:00", "2026-11-03T11:00:00-03:00")
    assert a.sobrepoe(b) is False
    assert b.sobrepoe(a) is False


def test_intervalos_disjuntos_nao_se_sobrepoem() -> None:
    a = Intervalo.a_partir_de_iso("2026-11-03T09:00:00-03:00", "2026-11-03T10:00:00-03:00")
    b = Intervalo.a_partir_de_iso("2026-11-03T11:00:00-03:00", "2026-11-03T12:00:00-03:00")
    assert a.sobrepoe(b) is False


def test_sala_guarda_atributos() -> None:
    sala = Sala(id="sala-aquario", nome="Aquario", capacidade=4, recursos=["tv"])
    assert sala.id == "sala-aquario"
    assert sala.capacidade == 4


def test_reserva_expoe_intervalo_a_partir_das_strings_originais() -> None:
    reserva = Reserva(
        id="res-0001",
        sala="sala-garagem",
        inicio="2026-11-03T14:00:00-03:00",
        fim="2026-11-03T15:00:00-03:00",
        responsavel="Marty",
    )
    assert reserva.intervalo.duracao() == timedelta(hours=1)
