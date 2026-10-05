"""MRTR (Multi-Round Tool Retry): resolver de elicitation para `reservar_sala`.

Ver ADR-0006 (notas da fase 002-mrtr): o resolver é só leitura (recalcula o
conflito a cada rodada); só a tool grava. `Elicit.schema` precisa ser uma
classe pydantic — por isso o enum dinâmico via `create_model`/`Literal`.
"""

from __future__ import annotations

from typing import Any, Literal

from mcp.server.mcpserver import Elicit
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field, create_model

from central_salas.application import casos_de_uso
from central_salas.constantes import MSG_ELICITATION
from central_salas.domain.erros import ErroDominio, ErroSemAlternativas
from central_salas.domain.modelos import Intervalo
from central_salas.infra.repositorio import RepositorioEmMemoria


def criar_resolver_escolha_de_sala(
    repositorio: RepositorioEmMemoria,
) -> Any:
    """Factory: cria o resolver `escolha_de_sala` com o repositório por closure."""

    def escolha_de_sala(sala: str, inicio: str, fim: str) -> Elicit[Any] | None:
        intervalo = Intervalo.a_partir_de_iso(inicio, fim)
        try:
            alternativas = casos_de_uso.verificar_conflito_reserva(repositorio, sala, intervalo)
        except ErroDominio as erro:
            raise ToolError(str(erro)) from erro

        if alternativas is None:
            return None
        if not alternativas:
            raise ToolError(str(ErroSemAlternativas()))

        esquema = create_model(
            "EscolhaDeSala",
            sala=(
                Literal[tuple(alternativas)],
                Field(description="Sala alternativa escolhida"),
            ),
        )
        return Elicit(MSG_ELICITATION, esquema)

    return escolha_de_sala
