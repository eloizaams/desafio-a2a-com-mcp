"""Servidor MCP fake (em processo) só para TDD do `ClienteSalas` (T3.2/T3.3).

Espelha o formato de `reservar_sala`/`politica://uso` do servidor real o
suficiente para exercitar os três ramos (livre, conflito, erro de domínio)
sem precisar de rede nem do pacote `central_salas` (sem import cruzado).
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from mcp.server.mcpserver import (
    AcceptedElicitation,
    CancelledElicitation,
    DeclinedElicitation,
    Elicit,
    ElicitationResult,
    MCPServer,
    Resolve,
)
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel, Field, create_model

SALA_OCUPADA = "sala-garagem"
SALA_INEXISTENTE = "sala-inexistente"
ALTERNATIVAS = ("sala-fusca", "sala-mirante")
MSG_ELICITATION = "A sala pedida esta ocupada nesse intervalo. Escolha uma alternativa."
TEXTO_POLITICA = "versao: 2026-11-01\n\n- regra de teste\n"


class ReservaOut(BaseModel):
    reserva: str | None = None
    reservado: bool = True
    sala: str | None = None
    inicio: str | None = None
    fim: str | None = None
    responsavel: str | None = None
    politica: str | None = None
    motivo: str | None = None


def criar_servidor_fake() -> MCPServer:
    servidor = MCPServer(name="fake-central-de-salas", version="0.0.0")

    @servidor.tool(name="listar_salas")
    def listar_salas() -> dict[str, Any]:
        return {"salas": []}

    def resolver_escolha(sala: str) -> Elicit[Any] | None:
        if sala == SALA_INEXISTENTE:
            raise ToolError(f"Sala inexistente: {sala}")
        if sala != SALA_OCUPADA:
            return None
        esquema = create_model(
            "EscolhaDeSala",
            sala=(Literal[ALTERNATIVAS], Field(description="Sala alternativa escolhida")),
        )
        return Elicit(MSG_ELICITATION, esquema)

    def reservar_sala(sala, inicio, fim, responsavel, escolha) -> ReservaOut:  # type: ignore[no-untyped-def]
        if isinstance(escolha, DeclinedElicitation | CancelledElicitation):
            return ReservaOut(reservado=False, motivo="recusado")
        assert isinstance(escolha, AcceptedElicitation)
        sala_final = sala if escolha.data is None else escolha.data.sala
        return ReservaOut(
            reserva="res-0001",
            reservado=True,
            sala=sala_final,
            inicio=inicio,
            fim=fim,
            responsavel=responsavel,
            politica="2026-11-01",
        )

    reservar_sala.__annotations__ = {
        "sala": str,
        "inicio": str,
        "fim": str,
        "responsavel": str,
        "escolha": Annotated[ElicitationResult[Any], Resolve(resolver_escolha)],
        "return": ReservaOut,
    }
    servidor.tool(name="reservar_sala")(reservar_sala)

    @servidor.resource("politica://uso", mime_type="text/markdown")
    def politica_de_uso() -> str:
        return TEXTO_POLITICA

    return servidor
