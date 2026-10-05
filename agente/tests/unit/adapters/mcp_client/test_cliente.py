import pytest
from mcp.server.mcpserver import MCPServer

from agente_salas.adapters.mcp_client.cliente import ClienteSalas, ErroDescoberta
from agente_salas.domain.pendencia import ArgsReserva, RespostaElicitation
from agente_salas.domain.resultados import Concluido, Falhou, PrecisaEntrada, Recusado
from agente_salas.domain.trace import iniciar

from .fake_servidor import ALTERNATIVAS, SALA_INEXISTENTE, SALA_OCUPADA, criar_servidor_fake

ARGS_LIVRE = ArgsReserva(
    sala="sala-aquario",
    inicio="2026-11-03T09:00:00-03:00",
    fim="2026-11-03T10:00:00-03:00",
    responsavel="Doc",
)
ARGS_CONFLITO = ArgsReserva(
    sala=SALA_OCUPADA,
    inicio="2026-11-03T14:00:00-03:00",
    fim="2026-11-03T15:00:00-03:00",
    responsavel="Marty",
)
ARGS_INEXISTENTE = ArgsReserva(
    sala=SALA_INEXISTENTE,
    inicio="2026-11-03T09:00:00-03:00",
    fim="2026-11-03T10:00:00-03:00",
    responsavel="Doc",
)


@pytest.fixture
def trace():  # type: ignore[no-untyped-def]
    return iniciar(None)


async def test_descobrir_encontra_reservar_sala() -> None:
    async with ClienteSalas(criar_servidor_fake()) as cliente:
        await cliente.descobrir()


async def test_descobrir_falha_quando_tool_nao_existe() -> None:
    servidor_vazio = MCPServer(name="vazio", version="0.0.0")
    async with ClienteSalas(servidor_vazio) as cliente:
        with pytest.raises(ErroDescoberta):
            await cliente.descobrir()


async def test_reservar_em_intervalo_livre_conclui(trace) -> None:  # type: ignore[no-untyped-def]
    async with ClienteSalas(criar_servidor_fake()) as cliente:
        await cliente.descobrir()
        resultado = await cliente.reservar(ARGS_LIVRE, trace)
    assert isinstance(resultado, Concluido)
    assert resultado.sala == "sala-aquario"
    assert resultado.reserva == "res-0001"


async def test_reservar_em_conflito_pede_entrada(trace) -> None:  # type: ignore[no-untyped-def]
    async with ClienteSalas(criar_servidor_fake()) as cliente:
        await cliente.descobrir()
        resultado = await cliente.reservar(ARGS_CONFLITO, trace)
    assert isinstance(resultado, PrecisaEntrada)
    assert set(resultado.pendencia.alternativas) == set(ALTERNATIVAS)
    assert isinstance(resultado.pendencia.request_state, str)
    assert resultado.pendencia.request_state != ""
    assert resultado.pendencia.chave != ""


async def test_reservar_sala_inexistente_falha(trace) -> None:  # type: ignore[no-untyped-def]
    async with ClienteSalas(criar_servidor_fake()) as cliente:
        await cliente.descobrir()
        resultado = await cliente.reservar(ARGS_INEXISTENTE, trace)
    assert isinstance(resultado, Falhou)
    assert f"Sala inexistente: {SALA_INEXISTENTE}" in resultado.mensagem


async def test_retomar_aceitando_alternativa_conclui(trace) -> None:  # type: ignore[no-untyped-def]
    async with ClienteSalas(criar_servidor_fake()) as cliente:
        await cliente.descobrir()
        pausado = await cliente.reservar(ARGS_CONFLITO, trace)
        assert isinstance(pausado, PrecisaEntrada)
        escolhida = pausado.pendencia.alternativas[0]
        resposta = RespostaElicitation(acao="accept", sala=escolhida)
        resultado = await cliente.retomar(ARGS_CONFLITO, pausado.pendencia, resposta, trace)
    assert isinstance(resultado, Concluido)
    assert resultado.sala == escolhida


async def test_retomar_recusando_conclui_recusado(trace) -> None:  # type: ignore[no-untyped-def]
    async with ClienteSalas(criar_servidor_fake()) as cliente:
        await cliente.descobrir()
        pausado = await cliente.reservar(ARGS_CONFLITO, trace)
        assert isinstance(pausado, PrecisaEntrada)
        resposta = RespostaElicitation(acao="decline")
        resultado = await cliente.retomar(ARGS_CONFLITO, pausado.pendencia, resposta, trace)
    assert isinstance(resultado, Recusado)
    assert resultado.motivo == "recusado"


async def test_versao_politica_le_primeira_linha(trace) -> None:  # type: ignore[no-untyped-def]
    async with ClienteSalas(criar_servidor_fake()) as cliente:
        versao = await cliente.versao_politica(trace)
    assert versao == "2026-11-01"
