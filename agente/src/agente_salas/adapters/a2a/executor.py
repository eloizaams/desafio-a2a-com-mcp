"""AgentExecutor: traduz o `Desfecho` da ponte em estados de Task A2A.

Task nova → `Ponte.iniciar`; Task existente (só pode estar em INPUT_REQUIRED,
o SDK recusa mensagem em Task terminal) → `Ponte.continuar`. Toda decisão de
pausa/retomada vive em `application/ponte.py` (ADR-0002).
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

from agente_salas.application.ponte import Desfecho, Pausado, Ponte
from agente_salas.domain.resultados import Concluido, Falhou, Recusado
from agente_salas.domain.trace import iniciar


class ErroRequisicaoSemMensagem(Exception):
    """`SendMessage` chegou ao executor sem `message` (o SDK deveria garantir isso)."""


class ExecutorReservaDeSala(AgentExecutor):
    """Executa a skill `reservar-sala` delegando à `Ponte`."""

    def __init__(self, ponte: Ponte) -> None:
        self._ponte = ponte

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        task_id = cast(str, context.task_id)
        updater = TaskUpdater(event_queue, task_id, cast(str, context.context_id))
        mensagem = context.message
        if mensagem is None:
            raise ErroRequisicaoSemMensagem
        texto = context.get_user_input()

        if context.current_task is None:
            await event_queue.enqueue_event(new_task_from_user_message(mensagem))
            await updater.start_work()
            trace = iniciar(_traceparent_recebido(context))
            desfecho = await self._ponte.iniciar(task_id, texto, trace)
        else:
            desfecho = await self._ponte.continuar(task_id, texto)
        await _publicar(updater, desfecho)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise UnsupportedOperationError()


async def _publicar(updater: TaskUpdater, desfecho: Desfecho) -> None:
    if isinstance(desfecho, Pausado):
        await updater.requires_input(message=_mensagem(updater, desfecho.texto))
    elif isinstance(desfecho, Concluido):
        await updater.add_artifact([Part(text=_artifact_reserva(desfecho))], name="reserva")
        await updater.complete()
    elif isinstance(desfecho, Recusado):
        await updater.cancel(message=_mensagem(updater, desfecho.motivo))
    elif isinstance(desfecho, Falhou):
        await _falhar(updater, desfecho.mensagem)


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
