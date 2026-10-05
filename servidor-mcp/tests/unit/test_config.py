import pytest

from central_salas.infra.config import ErroConfig, carregar_config

SEGREDO_VALIDO = "a" * 64


def test_usa_porta_padrao_quando_ausente() -> None:
    config = carregar_config({"REQUEST_STATE_SECRET": SEGREDO_VALIDO})
    assert config.porta == 7301


def test_le_porta_do_ambiente() -> None:
    config = carregar_config({"REQUEST_STATE_SECRET": SEGREDO_VALIDO, "MCP_PORT": "9000"})
    assert config.porta == 9000


def test_le_segredo_do_ambiente() -> None:
    config = carregar_config({"REQUEST_STATE_SECRET": SEGREDO_VALIDO})
    assert config.segredo_request_state == SEGREDO_VALIDO


def test_falha_sem_segredo() -> None:
    with pytest.raises(ErroConfig, match="REQUEST_STATE_SECRET"):
        carregar_config({})


def test_falha_com_segredo_curto() -> None:
    with pytest.raises(ErroConfig, match="32 bytes"):
        carregar_config({"REQUEST_STATE_SECRET": "a" * 31})


def test_falha_com_porta_nao_numerica() -> None:
    with pytest.raises(ErroConfig, match="MCP_PORT"):
        carregar_config({"REQUEST_STATE_SECRET": SEGREDO_VALIDO, "MCP_PORT": "abc"})
