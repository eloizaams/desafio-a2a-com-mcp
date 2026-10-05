from central_salas.domain.modelos import Reserva, Sala
from central_salas.infra.repositorio import RepositorioEmMemoria

SALAS = [Sala(id="sala-aquario", nome="Aquario", capacidade=4, recursos=["tv"])]
RESERVAS_SEED = [
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


def test_lista_salas_e_reservas_carregadas() -> None:
    repo = RepositorioEmMemoria(salas=SALAS, reservas=RESERVAS_SEED)
    assert repo.listar_salas() == SALAS
    assert repo.listar_reservas() == RESERVAS_SEED


def test_proxima_id_sequencial_apos_o_seed() -> None:
    repo = RepositorioEmMemoria(salas=SALAS, reservas=RESERVAS_SEED)
    assert repo.proxima_id() == "res-0003"


def test_proxima_id_comeca_em_res_0001_sem_seed() -> None:
    repo = RepositorioEmMemoria(salas=SALAS, reservas=[])
    assert repo.proxima_id() == "res-0001"


def test_adicionar_reserva_fica_visivel_para_proxima_consulta() -> None:
    repo = RepositorioEmMemoria(salas=SALAS, reservas=list(RESERVAS_SEED))
    nova = Reserva(
        id="res-0003",
        sala="sala-aquario",
        inicio="2026-11-03T09:00:00-03:00",
        fim="2026-11-03T10:00:00-03:00",
        responsavel="Doc",
    )
    repo.adicionar_reserva(nova)
    assert nova in repo.listar_reservas()
    assert repo.proxima_id() == "res-0004"
