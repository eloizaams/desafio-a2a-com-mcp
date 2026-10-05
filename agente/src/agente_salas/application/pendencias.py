"""Pendências MRTR por Task A2A, só em memória do agente (PONTE-02)."""

from __future__ import annotations

from dataclasses import dataclass

from agente_salas.domain.pendencia import ArgsReserva, PendenciaMRTR
from agente_salas.domain.trace import TraceContext


@dataclass(frozen=True)
class TaskPausada:
    """Tudo que a retomada precisa: a pendência opaca, os argumentos originais e o trace da Task."""

    pendencia: PendenciaMRTR
    args: ArgsReserva
    trace: TraceContext


class Pendencias:
    def __init__(self) -> None:
        self._por_task: dict[str, TaskPausada] = {}

    def obter(self, task_id: str) -> TaskPausada | None:
        return self._por_task.get(task_id)

    def guardar(self, task_id: str, pausa: TaskPausada) -> None:
        self._por_task[task_id] = pausa

    def remover(self, task_id: str) -> None:
        self._por_task.pop(task_id, None)
