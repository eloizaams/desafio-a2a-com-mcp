"""Builders de contexto que contornam duas limitações do `a2a-sdk==1.2.2`.

1. `ContextoComVersaoPadrao` supre o header `A2A-Version` ausente.

Limitação do `a2a-sdk` (constitution.md #10, documentar no README): o
dispatcher JSON-RPC v1.0 rejeita `SendMessage`/`GetTask` com `-32009` quando o
cliente não manda o header `A2A-Version: 1.0`, tratando a ausência como v0.3 —
mas o `enable_v0_3_compat` do SDK só entende os nomes de método da v0.3
(`message/send`, `tasks/get`, ...), não os da v1.0 usados aqui. Nem
`exemplos/wire/08-a2a-send-message.json` nem `validador/validar.py` mandam
esse header (não é exigido pelo enunciado), então o agente assume `1.0`
quando ele vier ausente, em vez de recusar um cliente v1.0 legítimo.

2. `ContextoDaTaskExistente` herda o `contextId` da Task numa continuação.

O `DefaultRequestHandlerV2` monta o `RequestContext` com `task=None` mesmo
quando a mensagem traz `taskId`; sem `contextId` na mensagem (o validador e
`exemplos/wire` mandam só `taskId`), `RequestContext` gera um UUID novo. A
mensagem do usuário entra no `history` com esse id falso e os eventos do
executor divergem do `TaskManager` (`InvalidParamsError: Context in event
doesn't match TaskManager`). A spec A2A diz que o `contextId` de uma Task
existente vale para a continuação, então ele é lido do `TaskStore`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from a2a.server.agent_execution import RequestContext, SimpleRequestContextBuilder
from a2a.server.context import ServerCallContext
from a2a.server.routes.common import DefaultServerCallContextBuilder
from a2a.utils.constants import PROTOCOL_VERSION_1_0, VERSION_HEADER

from agente_salas.constantes import ESTADO_HEADERS

if TYPE_CHECKING:
    from a2a.server.tasks import TaskStore
    from a2a.types import SendMessageRequest, Task
    from starlette.requests import Request


class ContextoComVersaoPadrao(DefaultServerCallContextBuilder):
    def build(self, request: Request) -> ServerCallContext:
        contexto = super().build(request)
        cabecalhos = contexto.state.setdefault(ESTADO_HEADERS, {})
        cabecalhos.setdefault(VERSION_HEADER, PROTOCOL_VERSION_1_0)
        return contexto


class ContextoDaTaskExistente(SimpleRequestContextBuilder):
    def __init__(self, task_store: TaskStore) -> None:
        super().__init__(task_store=task_store)

    async def build(
        self,
        context: ServerCallContext,
        params: SendMessageRequest | None = None,
        task_id: str | None = None,
        context_id: str | None = None,
        task: Task | None = None,
    ) -> RequestContext:
        if task_id and not context_id and self._task_store is not None:
            existente = await self._task_store.get(task_id, context)
            if existente is not None:
                context_id = existente.context_id
        return await super().build(context, params, task_id, context_id, task)
