"""Middleware: uma linha em stderr por request MCP (MCP-09)."""

from __future__ import annotations

import sys
from typing import Any

from mcp.server.context import CallNext, HandlerResult, ServerRequestContext


async def registrar_requisicao(
    ctx: ServerRequestContext[Any, Any], call_next: CallNext
) -> HandlerResult:
    meta = ctx.params.get("_meta") if ctx.params else None
    traceparent = (meta or {}).get("traceparent", "-")
    print(f"method={ctx.method} id={ctx.request_id} traceparent={traceparent}", file=sys.stderr)
    return await call_next(ctx)
