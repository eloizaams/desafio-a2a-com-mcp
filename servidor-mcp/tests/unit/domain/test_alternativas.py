from central_salas.domain.alternativas import alternativas
from central_salas.domain.modelos import Intervalo, Reserva, Sala

SALAS = [
    Sala(id="sala-aquario", nome="Aquario", capacidade=4, recursos=["tv"]),
    Sala(id="sala-porao", nome="Porao", capacidade=6, recursos=["quadro"]),
    Sala(id="sala-garagem", nome="Garagem", capacidade=12, recursos=["tv", "quadro"]),
    Sala(id="sala-fusca", nome="Fusca", capacidade=12, recursos=["tv"]),
    Sala(id="sala-mirante", nome="Mirante", capacidade=20, recursos=["tv", "quadro", "camera"]),
]

RESERVAS = [
    Reserva(
        id="res-0001",
        sala="sala-garagem",
        inicio="2026-11-03T14:00:00-03:00",
        fim="2026-11-03T15:00:00-03:00",
        responsavel="Marty",
    ),
    Reserva(
        id="res-0002",
        sala="sala-fusca",
        inicio="2026-11-03T16:00:00-03:00",
        fim="2026-11-03T17:00:00-03:00",
        responsavel="Jennifer",
    ),
]


def _intervalo(inicio: str, fim: str) -> Intervalo:
    return Intervalo.a_partir_de_iso(f"2026-11-03T{inicio}:00-03:00", f"2026-11-03T{fim}:00-03:00")


def test_caso_garagem_14_15_sugere_fusca_e_mirante_em_ordem_de_capacidade() -> None:
    sugeridas = alternativas(SALAS, RESERVAS, "sala-garagem", _intervalo("14:00", "15:00"))
    assert [s.id for s in sugeridas] == ["sala-fusca", "sala-mirante"]


def test_exclui_a_sala_pedida() -> None:
    sugeridas = alternativas(SALAS, RESERVAS, "sala-garagem", _intervalo("14:00", "15:00"))
    assert "sala-garagem" not in [s.id for s in sugeridas]


def test_exclui_salas_com_capacidade_menor() -> None:
    sugeridas = alternativas(SALAS, RESERVAS, "sala-garagem", _intervalo("14:00", "15:00"))
    assert "sala-aquario" not in [s.id for s in sugeridas]
    assert "sala-porao" not in [s.id for s in sugeridas]


def test_exclui_salas_ocupadas_no_intervalo() -> None:
    sugeridas = alternativas(SALAS, RESERVAS, "sala-garagem", _intervalo("16:00", "17:00"))
    assert "sala-fusca" not in [s.id for s in sugeridas]
    assert [s.id for s in sugeridas] == ["sala-mirante"]


def test_limita_a_tres_alternativas() -> None:
    salas_amplas = [
        *SALAS,
        Sala(id="sala-zz", nome="ZZ", capacidade=30, recursos=[]),
        Sala(id="sala-yy", nome="YY", capacidade=40, recursos=[]),
    ]
    sugeridas = alternativas(salas_amplas, RESERVAS, "sala-garagem", _intervalo("14:00", "15:00"))
    assert len(sugeridas) == 3
    assert [s.id for s in sugeridas] == ["sala-fusca", "sala-mirante", "sala-zz"]
