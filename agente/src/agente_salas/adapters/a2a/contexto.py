"""`ServerCallContextBuilder` que supre o header `A2A-Version` ausente.

Limitação do `a2a-sdk` (constitution.md #10, documentar no README): o
dispatcher JSON-RPC v1.0 rejeita `SendMessage`/`GetTask` com `-32009` quando o
cliente não manda o header `A2A-Version: 1.0`, tratando a ausência como v0.3 —
mas o `enable_v0_3_compat` do SDK só entende os nomes de método da v0.3
(`message/send`, `tasks/get`, ...), não os da v1.0 usados aqui. Nem
`exemplos/wire/08-a2a-send-message.json` nem `validador/validar.py` mandam
esse header (não é exigido pelo enunciado), então o agente assume `1.0`
quando ele vier ausente, em vez de recusar um cliente v1.0 legítimo.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from a2a.server.context import ServerCallContext
from a2a.server.routes.common import DefaultServerCallContextBuilder
from a2a.utils.constants import PROTOCOL_VERSION_1_0, VERSION_HEADER

if TYPE_CHECKING:
    from starlette.requests import Request


class ContextoComVersaoPadrao(DefaultServerCallContextBuilder):
    def build(self, request: Request) -> ServerCallContext:
        contexto = super().build(request)
        cabecalhos = contexto.state.setdefault("headers", {})
        cabecalhos.setdefault(VERSION_HEADER, PROTOCOL_VERSION_1_0)
        return contexto
