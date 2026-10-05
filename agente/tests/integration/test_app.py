from starlette.testclient import TestClient

from agente_salas.adapters.a2a.app import criar_app
from agente_salas.infra.config import ConfigAgente


def test_app_serve_agent_card() -> None:
    app = criar_app(ConfigAgente(porta=7300, mcp_url="http://127.0.0.1:7301/mcp"))
    with TestClient(app) as cliente:
        resposta = cliente.get("/.well-known/agent-card.json")
    assert resposta.status_code == 200
    assert resposta.json()["supportedInterfaces"][0]["url"] == "http://127.0.0.1:7300/a2a"
