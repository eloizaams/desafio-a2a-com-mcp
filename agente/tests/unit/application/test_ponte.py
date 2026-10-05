from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

import pytest

from agente_salas.application.pendencias import Pendencias
from agente_salas.application.ponte import ErroSemPendencia, Pausado, Ponte
from agente_salas.constantes import MSG_COMANDO_INVALIDO
from agente_salas.domain.pendencia import ArgsReserva, PendenciaMRTR, RespostaElicitation
from agente_salas.domain.resultados import Concluido, Falhou, PrecisaEntrada, Recusado
from agente_salas.domain.trace import TraceContext, iniciar

PEDIDO_OCUPADO = (
    "reservar sala=sala-garagem inicio=2026-11-03T14:00:00-03:00 "
    "fim=2026-11-03T15:00:00-03:00 responsavel=Marty"
)
LINHA_PAUSA = "alternativas: sala-fusca, sala-mirante"
ALTERNATIVAS = ("sala-fusca", "sala-mirante")

Resultado = Concluido | Falhou | Recusado | PrecisaEntrada


def _precisa_entrada(
    request_state: str = "estado-1", alternativas: tuple[str, ...] = ALTERNATIVAS
) -> PrecisaEntrada:
    return PrecisaEntrada(
        pendencia=PendenciaMRTR(
            chave="escolha_de_sala",
            campo="sala",
            alternativas=alternativas,
            request_state=request_state,
        ),
        mensagem="A sala pedida esta ocupada nesse intervalo. Escolha uma alternativa.",
    )


def _concluido(sala: str) -> Concluido:
    return Concluido(
        reserva="res-0001",
        sala=sala,
        inicio="2026-11-03T14:00:00-03:00",
        fim="2026-11-03T15:00:00-03:00",
        responsavel="Marty",
        politica="2026-11-01",
    )


@dataclass
class ChamadaRetomar:
    args: ArgsReserva
    pendencia: PendenciaMRTR
    resposta: RespostaElicitation
    trace: TraceContext


@dataclass
class ClienteFake:
    """Devolve, em ordem, os resultados roteirizados e registra cada chamada."""

    roteiro: list[Resultado]
    reservas: list[tuple[ArgsReserva, TraceContext]] = field(default_factory=list)
    retomadas: list[ChamadaRetomar] = field(default_factory=list)

    async def reservar(
        self, args: ArgsReserva, trace: TraceContext
    ) -> Concluido | Falhou | PrecisaEntrada:
        self.reservas.append((args, trace))
        resultado = self.roteiro.pop(0)
        assert not isinstance(resultado, Recusado)
        return resultado

    async def retomar(
        self,
        args: ArgsReserva,
        pendencia: PendenciaMRTR,
        resposta: RespostaElicitation,
        trace: TraceContext,
    ) -> Resultado:
        self.retomadas.append(ChamadaRetomar(args, pendencia, resposta, trace))
        return self.roteiro.pop(0)

    @property
    def chamadas(self) -> int:
        return len(self.reservas) + len(self.retomadas)


def _ponte(cliente: ClienteFake, pendencias: Pendencias | None = None) -> Ponte:
    @asynccontextmanager
    async def abrir() -> AsyncIterator[ClienteFake]:
        yield cliente

    return Ponte(abrir, pendencias or Pendencias())


TRACE = iniciar("00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01")


async def _pausar(ponte: Ponte, task_id: str = "task-1") -> None:
    assert await ponte.iniciar(task_id, PEDIDO_OCUPADO, TRACE) == Pausado(LINHA_PAUSA)


# --- iniciar -----------------------------------------------------------------


async def test_sala_livre_conclui_sem_guardar_pendencia() -> None:
    pendencias = Pendencias()
    ponte = _ponte(ClienteFake([_concluido("sala-garagem")]), pendencias)
    assert await ponte.iniciar("task-1", PEDIDO_OCUPADO, TRACE) == _concluido("sala-garagem")
    assert pendencias.obter("task-1") is None


async def test_falha_da_tool_vira_falhou_com_a_mensagem_exata() -> None:
    ponte = _ponte(ClienteFake([Falhou("Sala inexistente: sala-x")]))
    assert await ponte.iniciar("task-1", PEDIDO_OCUPADO, TRACE) == Falhou(
        "Sala inexistente: sala-x"
    )


@pytest.mark.parametrize("texto", ["oi tudo bem", "escolha=sala-fusca", "escolha=recusar"])
async def test_comando_invalido_para_task_nova_falha_sem_chamar_mcp(texto: str) -> None:
    cliente = ClienteFake([])
    assert await _ponte(cliente).iniciar("task-1", texto, TRACE) == Falhou(MSG_COMANDO_INVALIDO)
    assert cliente.chamadas == 0


async def test_pedido_vai_ao_mcp_com_os_argumentos_e_o_trace_da_task() -> None:
    cliente = ClienteFake([_concluido("sala-garagem")])
    await _ponte(cliente).iniciar("task-1", PEDIDO_OCUPADO, TRACE)
    ((args, trace),) = cliente.reservas
    assert args == ArgsReserva(
        "sala-garagem", "2026-11-03T14:00:00-03:00", "2026-11-03T15:00:00-03:00", "Marty"
    )
    assert trace.trace_id == TRACE.trace_id


async def test_conflito_pausa_com_a_linha_exata_na_ordem_do_enum() -> None:
    """PONTE-01."""
    ponte = _ponte(ClienteFake([_precisa_entrada()]))
    await _pausar(ponte)


async def test_conflito_guarda_pendencia_com_args_e_trace() -> None:
    """PONTE-02."""
    pendencias = Pendencias()
    await _pausar(_ponte(ClienteFake([_precisa_entrada()]), pendencias))
    pausa = pendencias.obter("task-1")
    assert pausa is not None
    assert pausa.pendencia == _precisa_entrada().pendencia
    assert pausa.args.sala == "sala-garagem"
    assert pausa.trace.trace_id == TRACE.trace_id


async def test_mesmo_pedido_em_conflito_produz_a_mesma_pausa() -> None:
    """PONTE-07."""
    ponte = _ponte(ClienteFake([_precisa_entrada("estado-1"), _precisa_entrada("estado-2")]))
    primeira = await ponte.iniciar("task-1", PEDIDO_OCUPADO, TRACE)
    segunda = await ponte.iniciar("task-2", PEDIDO_OCUPADO, TRACE)
    assert primeira == segunda == Pausado(LINHA_PAUSA)


# --- continuar ---------------------------------------------------------------


async def test_escolha_fora_das_alternativas_repausa_sem_chamar_mcp() -> None:
    """PONTE-03."""
    pendencias = Pendencias()
    cliente = ClienteFake([_precisa_entrada()])
    ponte = _ponte(cliente, pendencias)
    await _pausar(ponte)
    assert await ponte.continuar("task-1", "escolha=sala-aquario") == Pausado(LINHA_PAUSA)
    assert cliente.chamadas == 1
    assert pendencias.obter("task-1") is not None


@pytest.mark.parametrize("texto", ["oi", PEDIDO_OCUPADO, "escolha="])
async def test_continuacao_que_nao_e_escolha_repausa_sem_chamar_mcp(texto: str) -> None:
    """PONTE-09."""
    cliente = ClienteFake([_precisa_entrada()])
    ponte = _ponte(cliente)
    await _pausar(ponte)
    assert await ponte.continuar("task-1", texto) == Pausado(LINHA_PAUSA)
    assert cliente.chamadas == 1


async def test_escolha_valida_retoma_com_a_pendencia_guardada_e_conclui() -> None:
    """PONTE-04."""
    pendencias = Pendencias()
    cliente = ClienteFake([_precisa_entrada(), _concluido("sala-fusca")])
    ponte = _ponte(cliente, pendencias)
    await _pausar(ponte)

    assert await ponte.continuar("task-1", "escolha=sala-fusca") == _concluido("sala-fusca")

    (retomada,) = cliente.retomadas
    assert retomada.resposta == RespostaElicitation(acao="accept", sala="sala-fusca")
    assert retomada.pendencia.request_state == "estado-1"
    assert retomada.args == cliente.reservas[0][0]
    assert retomada.trace.trace_id == TRACE.trace_id
    assert pendencias.obter("task-1") is None


async def test_recusar_responde_decline_e_devolve_recusado() -> None:
    """PONTE-05."""
    pendencias = Pendencias()
    cliente = ClienteFake([_precisa_entrada(), Recusado("recusado")])
    ponte = _ponte(cliente, pendencias)
    await _pausar(ponte)

    assert await ponte.continuar("task-1", "escolha=recusar") == Recusado("recusado")
    assert cliente.retomadas[0].resposta == RespostaElicitation(acao="decline")
    assert pendencias.obter("task-1") is None


async def test_tasks_pausadas_retomam_cada_uma_com_seu_request_state() -> None:
    """PONTE-06."""
    cliente = ClienteFake(
        [
            _precisa_entrada("estado-a"),
            _precisa_entrada("estado-b"),
            _concluido("sala-mirante"),
            _concluido("sala-mirante"),
        ]
    )
    ponte = _ponte(cliente)
    await _pausar(ponte, "task-a")
    await _pausar(ponte, "task-b")

    await ponte.continuar("task-b", "escolha=sala-mirante")
    await ponte.continuar("task-a", "escolha=sala-mirante")

    estados = [r.pendencia.request_state for r in cliente.retomadas]
    assert estados == ["estado-b", "estado-a"]


async def test_retry_que_volta_input_required_substitui_a_pendencia() -> None:
    """PONTE-08."""
    pendencias = Pendencias()
    cliente = ClienteFake(
        [
            _precisa_entrada("estado-1"),
            _precisa_entrada("estado-2", alternativas=("sala-mirante",)),
        ]
    )
    ponte = _ponte(cliente, pendencias)
    await _pausar(ponte)

    resultado = await ponte.continuar("task-1", "escolha=sala-fusca")

    assert resultado == Pausado("alternativas: sala-mirante")
    pausa = pendencias.obter("task-1")
    assert pausa is not None and pausa.pendencia.request_state == "estado-2"


async def test_falha_no_retry_remove_a_pendencia() -> None:
    pendencias = Pendencias()
    cliente = ClienteFake([_precisa_entrada(), Falhou("Sala inexistente: sala-fusca")])
    ponte = _ponte(cliente, pendencias)
    await _pausar(ponte)

    assert await ponte.continuar("task-1", "escolha=sala-fusca") == Falhou(
        "Sala inexistente: sala-fusca"
    )
    assert pendencias.obter("task-1") is None


async def test_continuar_task_sem_pendencia_e_erro() -> None:
    with pytest.raises(ErroSemPendencia):
        await _ponte(ClienteFake([])).continuar("task-x", "escolha=sala-fusca")
