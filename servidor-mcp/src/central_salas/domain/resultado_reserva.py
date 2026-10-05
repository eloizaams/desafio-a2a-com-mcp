"""Resultado da gravação de uma reserva (caminho livre ou após escolha de alternativa)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Reservada:
    """Reserva efetivada: sala pedida ou alternativa escolhida, sem conflito.

    `politica` (versão vigente) é um detalhe de apresentação, não do domínio;
    quem monta a saída da tool (adapter) a preenche, não este caso de uso.
    """

    reserva: str
    sala: str
    inicio: str
    fim: str
    responsavel: str
