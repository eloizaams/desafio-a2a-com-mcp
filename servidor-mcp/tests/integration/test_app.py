"""Testes de integração ASGI espelhando os checks V01-V12 do validador."""

import json
from collections.abc import Mapping
from typing import Any

import pytest
from starlette.testclient import TestClient

from central_salas.adapters.mcp.server import criar_app
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
    nome: str | None = None,
    omitir: str | None = None,
    traceparent: str | None = None,
) -> tuple[dict[str, Any], dict[str, str]]:
    meta: dict[str, Any] = {
        "io.modelcontextprotocol/protocolVersion": PROTOCOLO,
        "io.modelcontextprotocol/clientCapabilities": CAP_COM_ELICITATION,
    }
    if traceparent:
        meta["traceparent"] = traceparent
    if omitir == "protocolVersion":
        meta.pop("io.modelcontextprotocol/protocolVersion")
    if omitir == "clientCapabilities":
        meta.pop("io.modelcontextprotocol/clientCapabilities")
    corpo = {"jsonrpc": "2.0", "id": 1, "method": metodo, "params": {**params, "_meta": meta}}
    cabecalhos = {
        "Accept": "application/json, text/event-stream",
        "MCP-Protocol-Version": PROTOCOLO,
        "Mcp-Method": metodo,
    }
    if nome:
        cabecalhos["Mcp-Name"] = nome
    return corpo, cabecalhos


def _chamar(metodo: str, params: Mapping[str, Any], **kw: Any) -> tuple[int, dict[str, Any]]:
    corpo, cabecalhos = _requisicao(metodo, params, **kw)
    with TestClient(_app(), base_url="http://127.0.0.1:7301") as cliente:
        resposta = cliente.post("/mcp", json=corpo, headers=cabecalhos)
    return resposta.status_code, resposta.json()


def _chamar_tool(nome: str, argumentos: Mapping[str, Any], **kw: Any) -> tuple[int, dict[str, Any]]:
    return _chamar("tools/call", {"name": nome, "arguments": argumentos}, nome=nome, **kw)


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
