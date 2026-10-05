"""Trace W3C (`traceparent`) propagado em todo request MCP de uma Task (HOST-04).

Mesmo trace-id da chamada A2A recebida (se houver), span-id novo a cada request.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass

_VERSAO = "00"
_FLAGS = "01"
_BYTES_TRACE_ID = 16
_BYTES_SPAN_ID = 8
_ZERO_TRACE_ID = "0" * (_BYTES_TRACE_ID * 2)
_ZERO_SPAN_ID = "0" * (_BYTES_SPAN_ID * 2)
_NUMERO_DE_PARTES_DO_TRACEPARENT = 4


@dataclass(frozen=True)
class TraceContext:
    trace_id: str
    span_id: str

    @property
    def traceparent(self) -> str:
        return f"{_VERSAO}-{self.trace_id}-{self.span_id}-{_FLAGS}"

    def com_novo_span(self) -> TraceContext:
        return TraceContext(trace_id=self.trace_id, span_id=_gerar_hex(_BYTES_SPAN_ID))


def iniciar(traceparent_recebido: str | None) -> TraceContext:
    """Contexto para uma nova Task: reaproveita o trace-id recebido (se válido), com span novo."""
    recebido = _parse(traceparent_recebido) if traceparent_recebido else None
    trace_id = recebido.trace_id if recebido else _gerar_hex(_BYTES_TRACE_ID)
    return TraceContext(trace_id=trace_id, span_id=_gerar_hex(_BYTES_SPAN_ID))


def _parse(valor: str) -> TraceContext | None:
    partes = valor.split("-")
    if len(partes) != _NUMERO_DE_PARTES_DO_TRACEPARENT:
        return None
    versao, trace_id, span_id, _flags = partes
    if versao != _VERSAO:
        return None
    if not _hex_de_tamanho(trace_id, _BYTES_TRACE_ID) or trace_id == _ZERO_TRACE_ID:
        return None
    if not _hex_de_tamanho(span_id, _BYTES_SPAN_ID) or span_id == _ZERO_SPAN_ID:
        return None
    return TraceContext(trace_id=trace_id, span_id=span_id)


def _hex_de_tamanho(valor: str, tamanho_bytes: int) -> bool:
    if len(valor) != tamanho_bytes * 2:
        return False
    try:
        int(valor, 16)
    except ValueError:
        return False
    return True


def _gerar_hex(tamanho_bytes: int) -> str:
    return secrets.token_hex(tamanho_bytes)
