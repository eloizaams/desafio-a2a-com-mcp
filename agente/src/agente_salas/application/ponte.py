"""A ponte: Task A2A ↔ ciclo MRTR de `reservar_sala` (ADR-0002, PLANO §2.2).

Ida: `input_required` do MCP → guarda a pendência por `task_id` → `Pausado`.
Volta: `escolha=<id>` na mesma Task → valida contra as alternativas guardadas →
`retomar` (o cliente manda id JSON-RPC novo e ecoa o `requestState` intacto).
Domínio (conflito, alternativas) é sempre do servidor; aqui só se traduz protocolo.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from agente_salas.application.pendencias import Pendencias, TaskPausada
from agente_salas.constantes import (
    MSG_COMANDO_INVALIDO,
    PREFIXO_ALTERNATIVAS,
    SEPARADOR_ALTERNATIVAS,
)
from agente_salas.domain.comando import RECUSAR, ErroComando, Escolha, PedidoReserva, parse
from agente_salas.domain.pendencia import ArgsReserva, PendenciaMRTR, RespostaElicitation
from agente_salas.domain.resultados import Concluido, Falhou, PrecisaEntrada, Recusado
from agente_salas.domain.trace import TraceContext


class ClienteReserva(Protocol):
    """O que a ponte usa do cliente MCP (real: `ClienteSalas`; fake nos testes)."""

    async def reservar(
        self, args: ArgsReserva, trace: TraceContext
    ) -> Concluido | Falhou | PrecisaEntrada: ...

    async def retomar(
        self,
        args: ArgsReserva,
        pendencia: PendenciaMRTR,
        resposta: RespostaElicitation,
        trace: TraceContext,
    ) -> Concluido | Falhou | Recusado | PrecisaEntrada: ...


@dataclass(frozen=True)
class Pausado:
    """A Task deve ficar em INPUT_REQUIRED com `texto` como mensagem de status."""

    texto: str


Desfecho = Concluido | Falhou | Recusado | Pausado


class ErroSemPendencia(Exception):
    """Continuação de uma Task que não tem pausa MRTR guardada."""


class Ponte:
    def __init__(self, cliente: ClienteReserva, pendencias: Pendencias) -> None:
        self._cliente = cliente
        self._pendencias = pendencias

    async def iniciar(self, task_id: str, texto: str, trace: TraceContext) -> Desfecho:
        """1ª mensagem de uma Task: só um pedido `reservar ...` é aceito."""
        try:
            comando = parse(texto)
        except ErroComando:
            return Falhou(MSG_COMANDO_INVALIDO)
        if not isinstance(comando, PedidoReserva):
            return Falhou(MSG_COMANDO_INVALIDO)

        args = _args(comando)
        resultado = await self._cliente.reservar(args, trace.com_novo_span())
        return self._desfecho(task_id, args, trace, resultado)

    async def continuar(self, task_id: str, texto: str) -> Desfecho:
        """Mensagem seguinte numa Task pausada: `escolha=<id>` ou `escolha=recusar`."""
        pausa = self._pendencias.obter(task_id)
        if pausa is None:
            raise ErroSemPendencia(task_id)

        resposta = _resposta(texto, pausa.pendencia.alternativas)
        if resposta is None:
            return _pausado(pausa.pendencia)

        resultado = await self._cliente.retomar(
            pausa.args, pausa.pendencia, resposta, pausa.trace.com_novo_span()
        )
        return self._desfecho(task_id, pausa.args, pausa.trace, resultado)

    def _desfecho(
        self,
        task_id: str,
        args: ArgsReserva,
        trace: TraceContext,
        resultado: Concluido | Falhou | Recusado | PrecisaEntrada,
    ) -> Desfecho:
        if isinstance(resultado, PrecisaEntrada):
            self._pendencias.guardar(task_id, TaskPausada(resultado.pendencia, args, trace))
            return _pausado(resultado.pendencia)
        self._pendencias.remover(task_id)
        return resultado


def _resposta(texto: str, alternativas: tuple[str, ...]) -> RespostaElicitation | None:
    """Traduz a continuação; `None` = não é uma escolha válida, a Task segue pausada."""
    try:
        comando = parse(texto)
    except ErroComando:
        return None
    if not isinstance(comando, Escolha):
        return None
    if comando.valor == RECUSAR:
        return RespostaElicitation(acao="decline")
    if comando.valor not in alternativas:
        return None
    return RespostaElicitation(acao="accept", sala=comando.valor)


def _pausado(pendencia: PendenciaMRTR) -> Pausado:
    return Pausado(PREFIXO_ALTERNATIVAS + SEPARADOR_ALTERNATIVAS.join(pendencia.alternativas))


def _args(pedido: PedidoReserva) -> ArgsReserva:
    return ArgsReserva(
        sala=pedido.sala, inicio=pedido.inicio, fim=pedido.fim, responsavel=pedido.responsavel
    )
