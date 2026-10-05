"""Erros de domínio: pedido de reserva recusado pela política.

Nomes seguem o domínio em português (``ErroX``, sem sufixo ``Error``); ver
constitution.md e DESAFIOS.md (ruff N818 desligado de propósito).
"""

from central_salas.constantes import (
    ERRO_DURACAO,
    ERRO_INTERVALO,
    ERRO_JANELA,
    ERRO_SALA_INEXISTENTE,
    ERRO_SEM_ALTERNATIVAS,
)


class ErroDominio(Exception):
    """Pedido de reserva recusado pela política do domínio."""


class ErroSalaInexistente(ErroDominio):
    def __init__(self, sala_id: str) -> None:
        super().__init__(ERRO_SALA_INEXISTENTE.format(sala_id=sala_id))


class ErroIntervaloInvertido(ErroDominio):
    def __init__(self) -> None:
        super().__init__(ERRO_INTERVALO)


class ErroJanela(ErroDominio):
    def __init__(self) -> None:
        super().__init__(ERRO_JANELA)


class ErroDuracao(ErroDominio):
    def __init__(self) -> None:
        super().__init__(ERRO_DURACAO)


class ErroSemAlternativas(ErroDominio):
    """Conflito sem alternativas disponíveis (fase 002-mrtr)."""

    def __init__(self) -> None:
        super().__init__(ERRO_SEM_ALTERNATIVAS)
