"""Montagem do servidor MCP (Streamable HTTP, stateless): tools, resource, log."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

from mcp.server.mcpserver import (
    AcceptedElicitation,
    CancelledElicitation,
    DeclinedElicitation,
    ElicitationResult,
    MCPServer,
    RequestStateSecurity,
    Resolve,
)
from mcp.server.mcpserver.exceptions import ToolError
from starlette.applications import Starlette

from central_salas.adapters.mcp.esquemas import (
    ConflitoOut,
    Disponibilidade,
    ListaDeSalas,
    ReservaOut,
    SalaOut,
)
from central_salas.adapters.mcp.log import registrar_requisicao
from central_salas.adapters.mcp.mrtr import criar_resolver_escolha_de_sala
from central_salas.application import casos_de_uso
from central_salas.constantes import (
    CAMINHO_MCP,
    CAMINHO_POLITICA,
    CAMINHO_RESERVAS,
    CAMINHO_SALAS,
    MOTIVO_RECUSA,
    NOME_SERVIDOR,
    TOOL_CONSULTAR_DISPONIBILIDADE,
    TOOL_LISTAR_SALAS,
    TOOL_RESERVAR_SALA,
    TTL_REQUEST_STATE_SEGUNDOS,
    URI_POLITICA,
    VERSAO_SERVIDOR,
)
from central_salas.domain.erros import ErroDominio
from central_salas.infra.config import ConfigServidor
from central_salas.infra.dados import carregar_politica, carregar_reservas, carregar_salas
from central_salas.infra.repositorio import RepositorioEmMemoria

DESCRICAO_LISTAR_SALAS = "Lista todas as salas com capacidade e recursos."
DESCRICAO_CONSULTAR_DISPONIBILIDADE = (
    "Diz se uma sala esta livre no intervalo, e quais reservas conflitam."
)
DESCRICAO_RESERVAR_SALA = (
    "Reserva uma sala. Se o intervalo estiver ocupado, pergunta qual alternativa usar."
)


def criar_app(config: ConfigServidor) -> Starlette:
    repositorio = RepositorioEmMemoria(
        salas=carregar_salas(Path(CAMINHO_SALAS)),
        reservas=carregar_reservas(Path(CAMINHO_RESERVAS)),
    )
    politica = carregar_politica(Path(CAMINHO_POLITICA))

    servidor = MCPServer(
        name=NOME_SERVIDOR,
        version=VERSAO_SERVIDOR,
        request_state_security=RequestStateSecurity(
            keys=[config.segredo_request_state],
            ttl=TTL_REQUEST_STATE_SEGUNDOS,
        ),
        middleware=[registrar_requisicao],
    )

    @servidor.tool(name=TOOL_LISTAR_SALAS, description=DESCRICAO_LISTAR_SALAS)
    def listar_salas() -> ListaDeSalas:
        salas = casos_de_uso.listar_salas(repositorio)
        return ListaDeSalas(
            salas=[
                SalaOut(id=s.id, nome=s.nome, capacidade=s.capacidade, recursos=s.recursos)
                for s in salas
            ]
        )

    @servidor.tool(
        name=TOOL_CONSULTAR_DISPONIBILIDADE, description=DESCRICAO_CONSULTAR_DISPONIBILIDADE
    )
    def consultar_disponibilidade(sala: str, inicio: str, fim: str) -> Disponibilidade:
        try:
            resultado = casos_de_uso.consultar_disponibilidade(repositorio, sala, inicio, fim)
        except ErroDominio as erro:
            raise ToolError(str(erro)) from erro
        return Disponibilidade(
            sala=resultado.sala,
            livre=resultado.livre,
            conflitos=[
                ConflitoOut(id=r.id, inicio=r.inicio, fim=r.fim, responsavel=r.responsavel)
                for r in resultado.conflitos
            ],
        )

    resolver_escolha_de_sala = criar_resolver_escolha_de_sala(repositorio)

    def reservar_sala(sala, inicio, fim, responsavel, escolha) -> ReservaOut:  # type: ignore[no-untyped-def]
        if isinstance(escolha, DeclinedElicitation | CancelledElicitation):
            return ReservaOut(reservado=False, motivo=MOTIVO_RECUSA)

        if not isinstance(escolha, AcceptedElicitation):
            raise ToolError(f"Resultado de elicitation inesperado: {type(escolha).__name__}")
        sala_final = sala if escolha.data is None else escolha.data.sala

        resultado = casos_de_uso.reservar_sala(repositorio, sala_final, inicio, fim, responsavel)
        return ReservaOut(
            reserva=resultado.reserva,
            reservado=True,
            sala=resultado.sala,
            inicio=resultado.inicio,
            fim=resultado.fim,
            responsavel=resultado.responsavel,
            politica=politica.versao,
            motivo=None,
        )

    # `sala`/`inicio`/`fim`/`responsavel` sem anotação na assinatura (acima) porque
    # `escolha` precisa referenciar `resolver_escolha_de_sala`, uma variável local do
    # closure: com `from __future__ import annotations` a anotação viraria string, e
    # `inspect.signature(fn, eval_str=True)` (usado pelo SDK para montar o inputSchema)
    # só resolve nomes em `fn.__globals__`, não no escopo local. Atribuir os tipos reais
    # direto em `__annotations__` evita a stringificação para este caso.
    reservar_sala.__annotations__ = {
        "sala": str,
        "inicio": str,
        "fim": str,
        "responsavel": str,
        "escolha": Annotated[ElicitationResult[Any], Resolve(resolver_escolha_de_sala)],
        "return": ReservaOut,
    }
    servidor.tool(name=TOOL_RESERVAR_SALA, description=DESCRICAO_RESERVAR_SALA)(reservar_sala)

    @servidor.resource(URI_POLITICA, mime_type="text/markdown")
    def politica_de_uso() -> str:
        return politica.texto

    return servidor.streamable_http_app(
        streamable_http_path=CAMINHO_MCP,
        stateless_http=True,
        json_response=True,
    )
