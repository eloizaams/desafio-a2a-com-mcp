from central_salas.domain.erros import (
    ErroDuracao,
    ErroIntervaloInvertido,
    ErroJanela,
    ErroSalaInexistente,
)
from central_salas.domain.modelos import Intervalo, Reserva, Sala
from central_salas.domain.politica import conflitos, validar_pedido

SALAS = [Sala(id="sala-aquario", nome="Aquario", capacidade=4, recursos=["tv"])]


def _intervalo(inicio: str, fim: str) -> Intervalo:
    return Intervalo.a_partir_de_iso(f"2026-11-03T{inicio}:00-03:00", f"2026-11-03T{fim}:00-03:00")


def test_sala_inexistente() -> None:
    erro = validar_pedido(SALAS, "sala-delorean", _intervalo("09:00", "10:00"))
    assert isinstance(erro, ErroSalaInexistente)
    assert str(erro) == "Sala inexistente: sala-delorean"


def test_fora_da_janela_antes_das_oito() -> None:
    erro = validar_pedido(SALAS, "sala-aquario", _intervalo("07:00", "08:00"))
    assert isinstance(erro, ErroJanela)


def test_duracao_acima_do_limite() -> None:
    erro = validar_pedido(SALAS, "sala-aquario", _intervalo("09:00", "12:00"))
    assert isinstance(erro, ErroDuracao)


def test_intervalo_invertido() -> None:
    erro = validar_pedido(SALAS, "sala-aquario", _intervalo("10:00", "09:00"))
    assert isinstance(erro, ErroIntervaloInvertido)


def test_pedido_valido_nao_tem_erro() -> None:
    erro = validar_pedido(SALAS, "sala-aquario", _intervalo("09:00", "10:00"))
    assert erro is None


def test_ordem_sala_antes_de_intervalo_invertido() -> None:
    erro = validar_pedido(SALAS, "sala-delorean", _intervalo("10:00", "09:00"))
    assert isinstance(erro, ErroSalaInexistente)


def test_ordem_intervalo_invertido_antes_de_janela() -> None:
    erro = validar_pedido(SALAS, "sala-aquario", _intervalo("08:00", "07:00"))
    assert isinstance(erro, ErroIntervaloInvertido)


def test_ordem_janela_antes_de_duracao() -> None:
    erro = validar_pedido(SALAS, "sala-aquario", _intervalo("07:00", "10:00"))
    assert isinstance(erro, ErroJanela)


def test_janela_aceita_limite_inicial() -> None:
    erro = validar_pedido(SALAS, "sala-aquario", _intervalo("08:00", "09:00"))
    assert erro is None


def test_janela_aceita_limite_final() -> None:
    erro = validar_pedido(SALAS, "sala-aquario", _intervalo("19:00", "20:00"))
    assert erro is None


def test_duracao_aceita_exatos_duas_horas() -> None:
    erro = validar_pedido(SALAS, "sala-aquario", _intervalo("09:00", "11:00"))
    assert erro is None


def test_conflitos_encontra_reservas_sobrepostas_na_mesma_sala() -> None:
    reservas = [
        Reserva(
            id="res-0001",
            sala="sala-garagem",
            inicio="2026-11-03T14:00:00-03:00",
            fim="2026-11-03T15:00:00-03:00",
            responsavel="Marty",
        ),
        Reserva(
            id="res-0002",
            sala="sala-aquario",
            inicio="2026-11-03T09:00:00-03:00",
            fim="2026-11-03T10:00:00-03:00",
            responsavel="Jennifer",
        ),
    ]
    encontrados = conflitos(reservas, "sala-aquario", _intervalo("09:30", "10:30"))
    assert [r.id for r in encontrados] == ["res-0002"]


def test_conflitos_vazio_quando_nao_ha_sobreposicao() -> None:
    reservas = [
        Reserva(
            id="res-0001",
            sala="sala-aquario",
            inicio="2026-11-03T09:00:00-03:00",
            fim="2026-11-03T10:00:00-03:00",
            responsavel="Jennifer",
        ),
    ]
    assert conflitos(reservas, "sala-aquario", _intervalo("10:00", "11:00")) == []
