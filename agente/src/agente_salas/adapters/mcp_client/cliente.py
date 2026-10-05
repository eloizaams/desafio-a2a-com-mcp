"""Cliente MCP do agente (ADR-0003): host do protocolo, nunca decide domínio.

`allow_input_required=True` em toda chamada — nunca `Client.call_tool` puro,
que roda o driver de retry e fecha o MRTR sozinho (ver DESAFIOS.md). O
`elicitation_callback` abaixo é só uma guarda: a capability só é anunciada se
existir um callback, e `allow_input_required=True` garante que ele nunca é
de fato chamado — se for, é bug.
"""

from __future__ import annotations

from types import TracebackType
from typing import Any, Self, cast

import mcp_types as types
from mcp import Client
from mcp.client.session import ClientRequestContext
from mcp.server.mcpserver import MCPServer

from agente_salas.constantes import (
    CLIENTE_MCP_NOME,
    PREFIXO_VERSAO_POLITICA,
    PROTOCOLO_MCP,
    TOOL_RESERVAR_SALA,
    URI_POLITICA,
    VERSAO_AGENTE,
)
from agente_salas.domain.pendencia import ArgsReserva, PendenciaMRTR, RespostaElicitation
from agente_salas.domain.resultados import Concluido, Falhou, PrecisaEntrada, Recusado
from agente_salas.domain.trace import TraceContext


class ErroDescoberta(Exception):
    """A tool esperada não apareceu em `tools/list` (HOST-01)."""


class ErroRespostaInesperada(Exception):
    """O servidor devolveu algo fora do contrato esperado para `reservar_sala`."""


async def _recusar_elicitation(
    context: ClientRequestContext, params: types.ElicitRequestParams
) -> types.ElicitResult | types.ErrorData:
    raise RuntimeError(
        "elicitation_callback chamado: o MRTR deveria sempre chegar como "
        "InputRequiredResult cru (allow_input_required=True), nunca por callback."
    )


class ClienteSalas:
    """Host MCP do agente: descoberta, leitura de política e o ciclo de `reservar_sala`.

    Uma instância vive o processo inteiro do agente (aberta no lifespan do app):
    o id JSON-RPC é monotônico por `Client`, então só assim o retry de uma Task
    sai com id novo (HOST-07) — um `Client` por Task recomeçaria em `id=1`.
    """

    def __init__(self, servidor: MCPServer | str) -> None:
        self._client = Client(
            servidor,
            mode=PROTOCOLO_MCP,
            client_info=types.Implementation(name=CLIENTE_MCP_NOME, version=VERSAO_AGENTE),
            elicitation_callback=_recusar_elicitation,
        )
        self._descoberto = False

    async def __aenter__(self) -> Self:
        await self._client.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self._client.__aexit__(exc_type, exc_val, exc_tb)

    async def descobrir(self) -> None:
        resultado = await self._client.session.list_tools()
        nomes = {tool.name for tool in resultado.tools}
        if TOOL_RESERVAR_SALA not in nomes:
            raise ErroDescoberta(f"tool {TOOL_RESERVAR_SALA!r} não encontrada em tools/list")
        self._descoberto = True

    async def versao_politica(self, trace: TraceContext) -> str:
        resultado = await self._client.session.read_resource(URI_POLITICA, meta=_meta(trace))
        texto = _primeiro_texto(resultado.contents)
        primeira_linha = texto.splitlines()[0] if texto else ""
        if not primeira_linha.startswith(PREFIXO_VERSAO_POLITICA):
            raise ErroRespostaInesperada(
                f"1ª linha da política sem {PREFIXO_VERSAO_POLITICA!r}: {primeira_linha!r}"
            )
        return primeira_linha.removeprefix(PREFIXO_VERSAO_POLITICA).strip()

    async def reservar(
        self, args: ArgsReserva, trace: TraceContext
    ) -> Concluido | Falhou | PrecisaEntrada:
        interpretado = await self._chamar_reservar_sala(args, trace)
        if isinstance(interpretado, Recusado):
            # Só pode vir de um retry (ver `retomar`): a 1ª chamada nunca carrega
            # `inputResponses`, então o servidor não tem como devolver `reservado=False`.
            raise ErroRespostaInesperada(
                f"reservar() recebeu Recusado sem retry: motivo={interpretado.motivo!r}"
            )
        return interpretado

    async def retomar(
        self,
        args: ArgsReserva,
        pendencia: PendenciaMRTR,
        resposta: RespostaElicitation,
        trace: TraceContext,
    ) -> Concluido | Falhou | Recusado | PrecisaEntrada:
        return await self._chamar_reservar_sala(
            args,
            trace,
            input_responses={pendencia.chave: _resposta_wire(pendencia, resposta)},
            request_state=pendencia.request_state,
        )

    async def _chamar_reservar_sala(
        self,
        args: ArgsReserva,
        trace: TraceContext,
        *,
        input_responses: types.InputResponses | None = None,
        request_state: str | None = None,
    ) -> Concluido | Falhou | Recusado | PrecisaEntrada:
        if not self._descoberto:
            await self.descobrir()
        resultado = await self._client.session.call_tool(
            TOOL_RESERVAR_SALA,
            _argumentos(args),
            input_responses=input_responses,
            request_state=request_state,
            meta=_meta(trace),
            allow_input_required=True,
        )
        return _interpretar(resultado)


def _meta(trace: TraceContext) -> types.RequestParamsMeta:
    # `RequestParamsMeta` é um TypedDict aberto (`extra_items=Any`, PEP 728); o mypy
    # 2.4 ainda não infere chaves extras num literal, daí o `cast` (ver DESAFIOS.md).
    return cast(types.RequestParamsMeta, {"traceparent": trace.traceparent})


def _argumentos(args: ArgsReserva) -> dict[str, Any]:
    return {
        "sala": args.sala,
        "inicio": args.inicio,
        "fim": args.fim,
        "responsavel": args.responsavel,
    }


def _resposta_wire(pendencia: PendenciaMRTR, resposta: RespostaElicitation) -> types.ElicitResult:
    if resposta.acao != "accept":
        return types.ElicitResult(action=resposta.acao)
    return types.ElicitResult(action="accept", content={pendencia.campo: resposta.sala})


def _interpretar(
    resultado: types.CallToolResult | types.InputRequiredResult,
) -> Concluido | Falhou | Recusado | PrecisaEntrada:
    if isinstance(resultado, types.InputRequiredResult):
        return _pedido_de_entrada(resultado)
    if resultado.is_error:
        return Falhou(mensagem=_primeiro_texto(resultado.content))
    conteudo = resultado.structured_content or {}
    if conteudo.get("reservado") is False:
        return Recusado(motivo=conteudo.get("motivo") or "")
    return Concluido(
        reserva=conteudo["reserva"],
        sala=conteudo["sala"],
        inicio=conteudo["inicio"],
        fim=conteudo["fim"],
        responsavel=conteudo["responsavel"],
        politica=conteudo.get("politica"),
    )


def _pedido_de_entrada(resultado: types.InputRequiredResult) -> PrecisaEntrada:
    if not resultado.input_requests:
        raise ErroRespostaInesperada("input_required sem input_requests")
    chave, pedido = next(iter(resultado.input_requests.items()))
    if not isinstance(pedido, types.ElicitRequest) or not isinstance(
        pedido.params, types.ElicitRequestFormParams
    ):
        raise ErroRespostaInesperada(f"input_request inesperado para {chave!r}: {pedido.method!r}")
    if resultado.request_state is None:
        # O MRTR deste servidor sempre sela o request_state junto com a elicitation
        # (ADR-0006); sem ele não há como retomar — retry com "" seria indistinguível
        # de um requestState adulterado, só que detectado tarde (no servidor) em vez de aqui.
        raise ErroRespostaInesperada(f"input_required sem requestState para {chave!r}")
    campo, definicao = next(iter(pedido.params.requested_schema["properties"].items()))
    alternativas = definicao.get("enum") or [definicao["const"]]
    return PrecisaEntrada(
        pendencia=PendenciaMRTR(
            chave=chave,
            campo=campo,
            alternativas=tuple(alternativas),
            request_state=resultado.request_state,
        ),
        mensagem=pedido.params.message,
    )


def _primeiro_texto(blocos: Any) -> str:
    for bloco in blocos:
        texto = getattr(bloco, "text", None)
        if texto is not None:
            return str(texto)
    return ""
