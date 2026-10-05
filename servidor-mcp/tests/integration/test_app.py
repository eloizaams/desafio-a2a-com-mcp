from starlette.testclient import TestClient

from central_salas.adapters.mcp.server import criar_app
from central_salas.infra.config import ConfigServidor

PROTOCOLO = "2026-07-28"


def test_app_responde_tools_list() -> None:
    app = criar_app(ConfigServidor(porta=7301, segredo_request_state="a" * 64))
    corpo = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {
            "_meta": {
                "io.modelcontextprotocol/protocolVersion": PROTOCOLO,
                "io.modelcontextprotocol/clientInfo": {"name": "teste", "version": "0"},
                "io.modelcontextprotocol/clientCapabilities": {},
            }
        },
    }
    cabecalhos = {
        "Accept": "application/json, text/event-stream",
        "MCP-Protocol-Version": PROTOCOLO,
        "Mcp-Method": "tools/list",
    }
    with TestClient(app, base_url="http://127.0.0.1:7301") as cliente:
        resposta = cliente.post("/mcp", json=corpo, headers=cabecalhos)
    assert resposta.status_code == 200
    assert resposta.json()["result"]["tools"] == []
