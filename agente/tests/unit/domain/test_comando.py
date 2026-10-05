import pytest

from agente_salas.domain.comando import RECUSAR, ErroComando, Escolha, PedidoReserva, parse


def test_parse_pedido_valido() -> None:
    texto = (
        "reservar sala=sala-garagem inicio=2026-11-03T14:00:00-03:00 "
        "fim=2026-11-03T15:00:00-03:00 responsavel=Marty"
    )
    assert parse(texto) == PedidoReserva(
        sala="sala-garagem",
        inicio="2026-11-03T14:00:00-03:00",
        fim="2026-11-03T15:00:00-03:00",
        responsavel="Marty",
    )


def test_parse_pedido_com_campos_em_ordem_trocada() -> None:
    texto = (
        "reservar responsavel=Marty fim=2026-11-03T15:00:00-03:00 "
        "inicio=2026-11-03T14:00:00-03:00 sala=sala-garagem"
    )
    assert parse(texto) == PedidoReserva(
        sala="sala-garagem",
        inicio="2026-11-03T14:00:00-03:00",
        fim="2026-11-03T15:00:00-03:00",
        responsavel="Marty",
    )


@pytest.mark.parametrize(
    "texto",
    [
        "reservar sala=sala-garagem inicio=2026-11-03T14:00:00-03:00 fim=2026-11-03T15:00:00-03:00",
        "reservar inicio=2026-11-03T14:00:00-03:00 fim=2026-11-03T15:00:00-03:00 responsavel=Marty",
        "reservar sala=sala-garagem fim=2026-11-03T15:00:00-03:00 responsavel=Marty",
        "reservar sala=sala-garagem inicio=2026-11-03T14:00:00-03:00 responsavel=Marty",
        "reservar",
        "",
    ],
)
def test_parse_pedido_com_campo_faltando_levanta_erro(texto: str) -> None:
    with pytest.raises(ErroComando):
        parse(texto)


def test_parse_pedido_com_campo_desconhecido_levanta_erro() -> None:
    texto = (
        "reservar sala=sala-garagem inicio=2026-11-03T14:00:00-03:00 "
        "fim=2026-11-03T15:00:00-03:00 responsavel=Marty extra=1"
    )
    with pytest.raises(ErroComando):
        parse(texto)


def test_parse_pedido_com_campo_repetido_levanta_erro() -> None:
    texto = (
        "reservar sala=sala-garagem sala=sala-fusca inicio=2026-11-03T14:00:00-03:00 "
        "fim=2026-11-03T15:00:00-03:00 responsavel=Marty"
    )
    with pytest.raises(ErroComando):
        parse(texto)


def test_parse_escolha_de_sala() -> None:
    assert parse("escolha=sala-fusca") == Escolha(valor="sala-fusca")


def test_parse_escolha_recusar() -> None:
    assert parse("escolha=recusar") == Escolha(valor=RECUSAR)


@pytest.mark.parametrize("texto", ["escolha=", "escolha", "escolha=sala-fusca extra"])
def test_parse_escolha_malformada_levanta_erro(texto: str) -> None:
    with pytest.raises(ErroComando):
        parse(texto)


def test_parse_texto_desconhecido_levanta_erro() -> None:
    with pytest.raises(ErroComando):
        parse("oi tudo bem")
