"""AgentExecutor: ponte entre `SendMessage`/`GetTask` e o `ClienteSalas` MCP.

Fase 4 cobre só o caminho inicial de uma Task nova: pedido válido → caminho
feliz ou falha de tool (A2A-04, A2A-05, A2A-08). A pausa MRTR
(`PrecisaEntrada` → `TASK_STATE_INPUT_REQUIRED`, retomada por `escolha=`) é a
ponte da fase 5 (`application/ponte.py`, ADR-0002).
"""

from __future__ import annotations

import json
from typing import cast

from a2a.helpers import new_task_from_user_message
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import Message, Part, TaskState
from a2a.utils.errors import UnsupportedOperationError
from mcp.server.mcpserver import MCPServer

from agente_salas.adapters.mcp_client.cliente import ClienteSalas
from agente_salas.constantes import MSG_COMANDO_INVALIDO
from agente_salas.domain.comando import ErroComando, Escolha, PedidoReserva, parse
from agente_salas.domain.pendencia import ArgsReserva
from agente_salas.domain.resultados import Concluido, Falhou, PrecisaEntrada
from agente_salas.domain.trace import iniciar


class ErroRequisicaoSemMensagem(Exception):
    """`SendMessage` chegou ao executor sem `message` (o SDK deveria garantir isso)."""


class ExecutorReservaDeSala(AgentExecutor):
    """Executa a skill `reservar-sala` contra o servidor MCP em `servidor`."""

    def __init__(self, servidor: MCPServer | str) -> None:
        self._servidor = servidor

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        updater = TaskUpdater(
            event_queue, cast(str, context.task_id), cast(str, context.context_id)
        )
        mensagem = context.message
        if mensagem is None:
            raise ErroRequisicaoSemMensagem
        await event_queue.enqueue_event(new_task_from_user_message(mensagem))

        try:
            comando = parse(context.get_user_input())
        except ErroComando:
            await _falhar(updater, MSG_COMANDO_INVALIDO)
            return
        if isinstance(comando, Escolha):
            # Sem Task pausada em memória na fase 4: nenhum `escolha=` é válido aqui.
            await _falhar(updater, MSG_COMANDO_INVALIDO)
            return

        await updater.start_work()
        await self._reservar(comando, context, updater)

    async def _reservar(
        self, pedido: PedidoReserva, context: RequestContext, updater: TaskUpdater
    ) -> None:
        trace = iniciar(_traceparent_recebido(context))
        args = ArgsReserva(
            sala=pedido.sala, inicio=pedido.inicio, fim=pedido.fim, responsavel=pedido.responsavel
        )
        async with ClienteSalas(self._servidor) as cliente:
            resultado = await cliente.reservar(args, trace.com_novo_span())

        if isinstance(resultado, Concluido):
            await updater.add_artifact([Part(text=_artifact_reserva(resultado))], name="reserva")
            await updater.complete()
        elif isinstance(resultado, Falhou):
            await _falhar(updater, resultado.mensagem)
        elif isinstance(resultado, PrecisaEntrada):
            raise NotImplementedError(
                "pausa MRTR (TASK_STATE_INPUT_REQUIRED) chega na fase 5 (a ponte)"
            )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise UnsupportedOperationError()


def _traceparent_recebido(context: RequestContext) -> str | None:
    cabecalhos = context.call_context.state.get("headers") or {}
    valor = cabecalhos.get("traceparent")
    return valor if isinstance(valor, str) else None


async def _falhar(updater: TaskUpdater, texto: str) -> None:
    """Termina a Task em FAILED com `texto` em `status.message` **e** em `history` (A2A-08).

    `TaskManager` só copia `status.message` para `history` quando um status
    *seguinte* o sobrescreve (`a2a/server/tasks/task_manager.py`); como FAILED
    é terminal, nada o sobrescreveria. Publicar a mesma mensagem num status
    WORKING antes do FAILED aciona essa cópia sem reabrir a Task.
    """
    mensagem = _mensagem(updater, texto)
    await updater.update_status(TaskState.TASK_STATE_WORKING, message=mensagem)
    await updater.failed(message=mensagem)


def _mensagem(updater: TaskUpdater, texto: str) -> Message:
    return updater.new_agent_message([Part(text=texto)])


def _artifact_reserva(resultado: Concluido) -> str:
    return json.dumps(
        {
            "reserva": resultado.reserva,
            "sala": resultado.sala,
            "inicio": resultado.inicio,
            "fim": resultado.fim,
            "responsavel": resultado.responsavel,
            "politica": resultado.politica,
        }
    )
