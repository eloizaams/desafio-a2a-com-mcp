"""Testes de integração ASGI espelhando os checks V01-V12 do validador."""

import json
from collections.abc import Mapping
from typing import Any

import pytest
from starlette.testclient import TestClient

from central_salas.adapters.mcp.server import criar_app
from central_salas.constantes import ERRO_SEM_ALTERNATIVAS, TTL_REQUEST_STATE_SEGUNDOS
from central_salas.infra.config import ConfigServidor

PROTOCOLO = "2026-07-28"
SEGREDO = "a" * 64
CAP_COM_ELICITATION = {"elicitation": {"form": {}}}


def _app() -> Any:
    return criar_app(ConfigServidor(porta=7301, segredo_request_state=SEGREDO))


def _requisicao(
    metodo: str,
    params: Mapping[str, Any],
    *,
    id_: int = 1,
    nome: str | None = None,
    omitir: str | None = None,
    traceparent: str | None = None,
    capabilities: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, str]]:
    meta: dict[str, Any] = {
        "io.modelcontextprotocol/protocolVersion": PROTOCOLO,
        "io.modelcontextprotocol/clientCapabilities": (
            CAP_COM_ELICITATION if capabilities is None else capabilities
        ),
    }
    if traceparent:
        meta["traceparent"] = traceparent
    if omitir == "protocolVersion":
        meta.pop("io.modelcontextprotocol/protocolVersion")
    if omitir == "clientCapabilities":
        meta.pop("io.modelcontextprotocol/clientCapabilities")
    corpo = {"jsonrpc": "2.0", "id": id_, "method": metodo, "params": {**params, "_meta": meta}}
    cabecalhos = {
        "Accept": "application/json, text/event-stream",
        "MCP-Protocol-Version": PROTOCOLO,
        "Mcp-Method": metodo,
    }
    if nome:
        cabecalhos["Mcp-Name"] = nome
    return corpo, cabecalhos


def _enviar(
    cliente: TestClient, metodo: str, params: Mapping[str, Any], **kw: Any
) -> tuple[int, dict[str, Any]]:
    corpo, cabecalhos = _requisicao(metodo, params, **kw)
    resposta = cliente.post("/mcp", json=corpo, headers=cabecalhos)
    return resposta.status_code, resposta.json()


def _chamar(metodo: str, params: Mapping[str, Any], **kw: Any) -> tuple[int, dict[str, Any]]:
    with TestClient(_app(), base_url="http://127.0.0.1:7301") as cliente:
        return _enviar(cliente, metodo, params, **kw)


def _chamar_tool(nome: str, argumentos: Mapping[str, Any], **kw: Any) -> tuple[int, dict[str, Any]]:
    return _chamar("tools/call", {"name": nome, "arguments": argumentos}, nome=nome, **kw)


def _reservar(
    cliente: TestClient, sala: str, inicio: str, fim: str, responsavel: str = "Doc", **kw: Any
) -> tuple[int, dict[str, Any]]:
    return _enviar(
        cliente,
        "tools/call",
        {
            "name": "reservar_sala",
            "arguments": {"sala": sala, "inicio": inicio, "fim": fim, "responsavel": responsavel},
        },
        nome="reservar_sala",
        **kw,
    )


def _retomar(
    cliente: TestClient,
    sala: str,
    inicio: str,
    fim: str,
    chave: str,
    resposta_elicitation: Mapping[str, Any],
    request_state: str,
    responsavel: str = "Doc",
    **kw: Any,
) -> tuple[int, dict[str, Any]]:
    return _enviar(
        cliente,
        "tools/call",
        {
            "name": "reservar_sala",
            "arguments": {"sala": sala, "inicio": inicio, "fim": fim, "responsavel": responsavel},
            "inputResponses": {chave: resposta_elicitation},
            "requestState": request_state,
        },
        nome="reservar_sala",
        **kw,
    )


def _texto(resultado: Mapping[str, Any]) -> str:
    return " ".join(p.get("text", "") for p in resultado.get("content", []))


def test_v01_tools_list_traz_as_tres_tools() -> None:
    _, resposta = _chamar("tools/list", {})
    nomes = {t["name"] for t in resposta["result"]["tools"]}
    assert nomes == {"listar_salas", "consultar_disponibilidade", "reservar_sala"}


def test_v02_toda_tool_tem_input_schema_objeto() -> None:
    _, resposta = _chamar("tools/list", {})
    assert all(t["inputSchema"]["type"] == "object" for t in resposta["result"]["tools"])


def test_v03_listar_salas_structured_content_igual_ao_texto() -> None:
    _, resposta = _chamar_tool("listar_salas", {})
    resultado = resposta["result"]
    assert json.loads(_texto(resultado)) == resultado["structuredContent"]
    assert {s["id"] for s in resultado["structuredContent"]["salas"]} >= {
        "sala-aquario",
        "sala-garagem",
    }


def test_v04_meta_sem_protocol_version_devolve_32602_e_http_400() -> None:
    status, resposta = _chamar_tool("listar_salas", {}, omitir="protocolVersion")
    assert status == 400
    assert resposta["error"]["code"] == -32602


def test_v05_meta_sem_client_capabilities_devolve_32602_e_http_400() -> None:
    status, resposta = _chamar_tool("listar_salas", {}, omitir="clientCapabilities")
    assert status == 400
    assert resposta["error"]["code"] == -32602


def test_v06_tool_inexistente_e_recusada() -> None:
    _, resposta = _chamar_tool("voar_delorean", {})
    recusou = (
        resposta.get("error", {}).get("code") == -32602
        or resposta.get("result", {}).get("isError") is True
    )
    assert recusou


def test_v07_resources_read_politica_de_uso() -> None:
    _, resposta = _chamar("resources/read", {"uri": "politica://uso"}, nome="politica://uso")
    conteudo = resposta["result"]["contents"][0]
    assert conteudo["mimeType"] == "text/markdown"
    assert "2026-11-01" in conteudo["text"]


def test_v08_resources_read_uri_inexistente_devolve_32602() -> None:
    _, resposta = _chamar(
        "resources/read", {"uri": "politica://inexistente"}, nome="politica://inexistente"
    )
    assert resposta["error"]["code"] == -32602


def test_v09_sala_inexistente_is_error_mensagem_exata() -> None:
    _, resposta = _chamar_tool(
        "reservar_sala",
        {
            "sala": "sala-delorean",
            "inicio": "2026-11-03T09:00:00-03:00",
            "fim": "2026-11-03T10:00:00-03:00",
            "responsavel": "Doc",
        },
    )
    resultado = resposta["result"]
    assert resultado["isError"] is True
    assert "Sala inexistente: sala-delorean" in _texto(resultado)


def test_v10_fora_da_janela_is_error_mensagem_exata() -> None:
    _, resposta = _chamar_tool(
        "consultar_disponibilidade",
        {
            "sala": "sala-aquario",
            "inicio": "2026-11-03T07:00:00-03:00",
            "fim": "2026-11-03T08:00:00-03:00",
        },
    )
    resultado = resposta["result"]
    assert resultado["isError"] is True
    assert "Fora da janela de uso: a politica permite reservas entre 08:00 e 20:00" in _texto(
        resultado
    )


def test_v11_duracao_acima_de_2h_is_error_mensagem_exata() -> None:
    _, resposta = _chamar_tool(
        "consultar_disponibilidade",
        {
            "sala": "sala-aquario",
            "inicio": "2026-11-03T09:00:00-03:00",
            "fim": "2026-11-03T12:00:00-03:00",
        },
    )
    resultado = resposta["result"]
    assert resultado["isError"] is True
    assert "Duracao acima do limite: a politica permite no maximo 2 horas" in _texto(resultado)


def test_v12_intervalo_invertido_is_error_mensagem_exata() -> None:
    _, resposta = _chamar_tool(
        "consultar_disponibilidade",
        {
            "sala": "sala-aquario",
            "inicio": "2026-11-03T10:00:00-03:00",
            "fim": "2026-11-03T09:00:00-03:00",
        },
    )
    resultado = resposta["result"]
    assert resultado["isError"] is True
    assert "Intervalo invalido: fim deve ser posterior a inicio" in _texto(resultado)


def test_mcp06_reservar_em_intervalo_livre_cria_reserva_sequencial_e_completa() -> None:
    _, resposta = _chamar_tool(
        "reservar_sala",
        {
            "sala": "sala-aquario",
            "inicio": "2026-11-03T09:00:00-03:00",
            "fim": "2026-11-03T10:00:00-03:00",
            "responsavel": "Doc",
        },
    )
    resultado = resposta["result"]
    assert resultado["isError"] is False
    estruturado = resultado["structuredContent"]
    assert estruturado["reserva"] == "res-0003"
    assert estruturado["reservado"] is True
    assert estruturado["politica"] == "2026-11-01"
    assert estruturado["motivo"] is None
    assert json.loads(_texto(resultado)) == estruturado


def test_mcp06_consultar_disponibilidade_devolve_livre_e_conflitos() -> None:
    _, resposta = _chamar_tool(
        "consultar_disponibilidade",
        {
            "sala": "sala-garagem",
            "inicio": "2026-11-03T14:30:00-03:00",
            "fim": "2026-11-03T15:30:00-03:00",
        },
    )
    estruturado = resposta["result"]["structuredContent"]
    assert estruturado["livre"] is False
    assert [c["id"] for c in estruturado["conflitos"]] == ["res-0001"]


def test_mcp06_reserva_fica_visivel_na_consulta_seguinte_no_mesmo_processo() -> None:
    app = _app()
    corpo_reserva, cabecalhos_reserva = _requisicao(
        "tools/call",
        {
            "name": "reservar_sala",
            "arguments": {
                "sala": "sala-aquario",
                "inicio": "2026-11-03T09:00:00-03:00",
                "fim": "2026-11-03T10:00:00-03:00",
                "responsavel": "Doc",
            },
        },
        nome="reservar_sala",
    )
    corpo_consulta, cabecalhos_consulta = _requisicao(
        "tools/call",
        {
            "name": "consultar_disponibilidade",
            "arguments": {
                "sala": "sala-aquario",
                "inicio": "2026-11-03T09:00:00-03:00",
                "fim": "2026-11-03T10:00:00-03:00",
            },
        },
        nome="consultar_disponibilidade",
    )
    with TestClient(app, base_url="http://127.0.0.1:7301") as cliente:
        cliente.post("/mcp", json=corpo_reserva, headers=cabecalhos_reserva)
        resposta = cliente.post("/mcp", json=corpo_consulta, headers=cabecalhos_consulta)
    estruturado = resposta.json()["result"]["structuredContent"]
    assert estruturado["livre"] is False
    assert [c["id"] for c in estruturado["conflitos"]] == ["res-0003"]


def test_mcp09_log_stderr_traz_method_id_traceparent(capsys: pytest.CaptureFixture[str]) -> None:
    traceparent = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
    _chamar("tools/list", {}, traceparent=traceparent)
    linha = capsys.readouterr().err
    assert "method=tools/list" in linha
    assert "id=1" in linha
    assert traceparent in linha


# MRTR (V13-V20): conflito -> input_required -> retry. Dataset de dados/*.json:
# sala-garagem ocupada 14h-15h (res-0001), sala-fusca ocupada 16h-17h (res-0002).


def _pendencia(resultado: Mapping[str, Any]) -> tuple[str, str]:
    pedidos = resultado["inputRequests"]
    chave = next(iter(pedidos))
    return chave, resultado["requestState"]


def test_v13_conflito_devolve_input_required_com_inputrequests_e_requeststate() -> None:
    _, resposta = _chamar_tool(
        "reservar_sala",
        {
            "sala": "sala-garagem",
            "inicio": "2026-11-03T14:00:00-03:00",
            "fim": "2026-11-03T15:00:00-03:00",
            "responsavel": "Marty",
        },
    )
    resultado = resposta["result"]
    assert resultado["resultType"] == "input_required"
    chave, estado = _pendencia(resultado)
    assert chave
    assert estado


def test_v14_elicitation_e_form_mode_com_alternativas_na_ordem_certa() -> None:
    _, resposta = _chamar_tool(
        "reservar_sala",
        {
            "sala": "sala-garagem",
            "inicio": "2026-11-03T14:00:00-03:00",
            "fim": "2026-11-03T15:00:00-03:00",
            "responsavel": "Marty",
        },
    )
    chave, _ = _pendencia(resposta["result"])
    pedido = resposta["result"]["inputRequests"][chave]["params"]
    assert pedido["mode"] == "form"
    assert pedido["requestedSchema"]["properties"]["sala"]["enum"] == [
        "sala-fusca",
        "sala-mirante",
    ]


def test_v15_conflito_sem_capability_elicitation_devolve_32021_e_http_400() -> None:
    status, resposta = _chamar_tool(
        "reservar_sala",
        {
            "sala": "sala-garagem",
            "inicio": "2026-11-03T14:00:00-03:00",
            "fim": "2026-11-03T15:00:00-03:00",
            "responsavel": "Marty",
        },
        capabilities={},
    )
    assert status == 400
    assert resposta["error"]["code"] == -32021
    assert "requiredCapabilities" in resposta["error"]["data"]


def test_v16_retry_com_inputresponses_e_requeststate_conclui_a_reserva() -> None:
    with TestClient(_app(), base_url="http://127.0.0.1:7301") as cliente:
        _, pausa = _reservar(
            cliente, "sala-fusca", "2026-11-03T16:00:00-03:00", "2026-11-03T17:00:00-03:00"
        )
        chave, estado = _pendencia(pausa["result"])
        _, resposta = _retomar(
            cliente,
            "sala-fusca",
            "2026-11-03T16:00:00-03:00",
            "2026-11-03T17:00:00-03:00",
            chave,
            {"action": "accept", "content": {"sala": "sala-garagem"}},
            estado,
            id_=2,
        )
    resultado = resposta["result"]
    assert resultado["resultType"] == "complete"
    assert resultado["isError"] is False
    assert resultado["structuredContent"]["sala"] == "sala-garagem"
    assert resultado["structuredContent"]["reservado"] is True


def test_v17_requeststate_adulterado_e_rejeitado_com_32602() -> None:
    with TestClient(_app(), base_url="http://127.0.0.1:7301") as cliente:
        _, pausa = _reservar(
            cliente, "sala-garagem", "2026-11-03T14:00:00-03:00", "2026-11-03T15:00:00-03:00"
        )
        chave, estado = _pendencia(pausa["result"])
        adulterado = estado[:-6] + ("AAAAAA" if not estado.endswith("AAAAAA") else "BBBBBB")
        _, resposta = _retomar(
            cliente,
            "sala-garagem",
            "2026-11-03T14:00:00-03:00",
            "2026-11-03T15:00:00-03:00",
            chave,
            {"action": "accept", "content": {"sala": "sala-fusca"}},
            adulterado,
            id_=2,
        )
    assert resposta["error"]["code"] == -32602


def test_v18_argumentos_adulterados_no_retry_nao_tomam_efeito() -> None:
    with TestClient(_app(), base_url="http://127.0.0.1:7301") as cliente:
        _reservar(
            cliente,
            "sala-garagem",
            "2026-11-03T09:00:00-03:00",
            "2026-11-03T10:00:00-03:00",
            responsavel="Ocupante",
        )
        _, pausa = _reservar(
            cliente,
            "sala-garagem",
            "2026-11-03T09:00:00-03:00",
            "2026-11-03T10:00:00-03:00",
            responsavel="Doc",
            id_=2,
        )
        chave, estado = _pendencia(pausa["result"])
        _, resposta = _retomar(
            cliente,
            "sala-mirante",
            "2026-11-03T13:00:00-03:00",
            "2026-11-03T14:00:00-03:00",
            chave,
            {"action": "accept", "content": {"sala": "sala-fusca"}},
            estado,
            responsavel="Biff",
            id_=3,
        )
    # O SDK vincula o requestState a um digest de todos os argumentos selados
    # (`_request_identity`); argumentos diferentes no retry mudam o digest e o
    # pedido inteiro e rejeitado — nunca executa com os valores adulterados.
    assert resposta["error"]["code"] == -32602


def test_v19_recusa_conclui_sem_reservar_e_sem_iserror() -> None:
    with TestClient(_app(), base_url="http://127.0.0.1:7301") as cliente:
        _, pausa = _reservar(
            cliente, "sala-garagem", "2026-11-03T14:00:00-03:00", "2026-11-03T15:00:00-03:00"
        )
        chave, estado = _pendencia(pausa["result"])
        _, resposta = _retomar(
            cliente,
            "sala-garagem",
            "2026-11-03T14:00:00-03:00",
            "2026-11-03T15:00:00-03:00",
            chave,
            {"action": "decline"},
            estado,
            id_=2,
        )
    resultado = resposta["result"]
    estruturado = resultado["structuredContent"]
    assert resultado["resultType"] == "complete"
    assert resultado["isError"] is False
    assert estruturado == {
        "reserva": None,
        "reservado": False,
        "sala": None,
        "inicio": None,
        "fim": None,
        "responsavel": None,
        "politica": None,
        "motivo": "recusado",
    }


def test_v20_conflito_sem_alternativa_possivel_devolve_iserror_com_mensagem_exata() -> None:
    with TestClient(_app(), base_url="http://127.0.0.1:7301") as cliente:
        _reservar(cliente, "sala-mirante", "2026-11-03T11:00:00-03:00", "2026-11-03T12:00:00-03:00")
        _, resposta = _reservar(
            cliente,
            "sala-mirante",
            "2026-11-03T11:00:00-03:00",
            "2026-11-03T12:00:00-03:00",
            id_=2,
        )
    resultado = resposta["result"]
    assert resultado["isError"] is True
    assert ERRO_SEM_ALTERNATIVAS in _texto(resultado)


def test_mrtr_retry_sobrevive_a_restart_do_processo() -> None:
    """T2.6: nada em memoria entre pausa e retry — processo A pausa, processo B conclui."""
    with TestClient(_app(), base_url="http://127.0.0.1:7301") as processo_a:
        _, pausa = _reservar(
            processo_a, "sala-garagem", "2026-11-03T14:00:00-03:00", "2026-11-03T15:00:00-03:00"
        )
    chave, estado = _pendencia(pausa["result"])

    with TestClient(_app(), base_url="http://127.0.0.1:7301") as processo_b:
        _, resposta = _retomar(
            processo_b,
            "sala-garagem",
            "2026-11-03T14:00:00-03:00",
            "2026-11-03T15:00:00-03:00",
            chave,
            {"action": "accept", "content": {"sala": "sala-fusca"}},
            estado,
            id_=2,
        )
    resultado = resposta["result"]
    assert resultado["resultType"] == "complete"
    assert resultado["isError"] is False
    assert resultado["structuredContent"]["sala"] == "sala-fusca"


class _RelogioFalso:
    """Substitui `time.time()` dentro de `mcp.server.request_state` (T2.6: expiração)."""

    def __init__(self, agora: float) -> None:
        self.agora = agora

    def time(self) -> float:
        return self.agora


def test_mrtr_requeststate_expirado_e_rejeitado_com_32602(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    relogio = _RelogioFalso(1_762_000_000.0)
    monkeypatch.setattr("mcp.server.request_state.time", relogio)

    with TestClient(_app(), base_url="http://127.0.0.1:7301") as cliente:
        _, pausa = _reservar(
            cliente, "sala-garagem", "2026-11-03T14:00:00-03:00", "2026-11-03T15:00:00-03:00"
        )
        chave, estado = _pendencia(pausa["result"])

        relogio.agora += TTL_REQUEST_STATE_SEGUNDOS + 1
        _, resposta = _retomar(
            cliente,
            "sala-garagem",
            "2026-11-03T14:00:00-03:00",
            "2026-11-03T15:00:00-03:00",
            chave,
            {"action": "accept", "content": {"sala": "sala-fusca"}},
            estado,
            id_=2,
        )
    assert resposta["error"]["code"] == -32602
