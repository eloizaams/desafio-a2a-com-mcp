import pytest

from agente_salas.infra.config import ErroConfig, carregar_config


def test_usa_padroes_quando_ambiente_vazio() -> None:
    config = carregar_config({})
    assert config.porta == 7300
    assert config.mcp_url == "http://127.0.0.1:7301/mcp"


def test_le_valores_do_ambiente() -> None:
    config = carregar_config({"AGENTE_PORT": "8000", "MCP_URL": "http://outro:1/mcp"})
    assert config.porta == 8000
    assert config.mcp_url == "http://outro:1/mcp"


def test_falha_com_porta_nao_numerica() -> None:
    with pytest.raises(ErroConfig, match="AGENTE_PORT"):
        carregar_config({"AGENTE_PORT": "abc"})
