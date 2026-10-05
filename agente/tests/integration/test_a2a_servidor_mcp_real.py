"""T4.6: o app A2A do agente contra um servidor MCP real, em subprocesso.

Espelha os checks V21-V26, V31 e V35 do validador (card, caminho feliz,
GetTask, Task terminal recusa SendMessage, sala inexistente -> FAILED).
"""

from __future__ import annotations

import json
import os
import secrets
import socket
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from agente_salas.adapters.a2a.app import criar_app
from agente_salas.infra.config import ConfigAgente

RAIZ = Path(__file__).resolve().parents[3]
PORTA_MCP = 7392


def _porta_aberta(porta: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as soquete:
        return soquete.connect_ex(("127.0.0.1", porta)) == 0


def _esperar_porta(porta: int, tentativas: int = 50) -> None:
    for _ in range(tentativas):
        if _porta_aberta(porta):
            return
        time.sleep(0.1)
    raise RuntimeError(f"servidor MCP não respondeu na porta {porta}")


@pytest.fixture
def servidor_mcp_real() -> Iterator[str]:
    ambiente = {
        **os.environ,
        "REQUEST_STATE_SECRET": secrets.token_hex(32),
        "MCP_PORT": str(PORTA_MCP),
    }
    processo = subprocess.Popen(
        ["uv", "run", "--package", "servidor-mcp", "python", "-m", "central_salas"],
        cwd=RAIZ,
        env=ambiente,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _esperar_porta(PORTA_MCP)
        yield f"http://127.0.0.1:{PORTA_MCP}/mcp"
    finally:
        processo.terminate()
        try:
            processo.wait(timeout=10)
        except subprocess.TimeoutExpired:
            processo.kill()
            processo.wait(timeout=10)


def _enviar(cliente: TestClient, texto: str, task_id: str | None = None) -> dict:
    mensagem: dict = {"messageId": "m1", "role": "ROLE_USER", "parts": [{"text": texto}]}
    if task_id:
        mensagem["taskId"] = task_id
    resposta = cliente.post(
        "/a2a",
        json={"jsonrpc": "2.0", "id": 1, "method": "SendMessage", "params": {"message": mensagem}},
    )
    assert resposta.status_code == 200
    return resposta.json()


def test_fluxo_a2a_completo_contra_mcp_real(servidor_mcp_real: str) -> None:
    config = ConfigAgente(porta=7300, mcp_url=servidor_mcp_real)
    app = criar_app(config)

    with TestClient(app) as cliente:
        # V21-V23: agent card já é coberto por unit/adapters/a2a/test_card.py
        # contra exemplos/wire/07; aqui exercitamos o fluxo de Task.

        # V24, V25: sala livre conclui a Task com o artifact da reserva.
        corpo = _enviar(
            cliente,
            "reservar sala=sala-porao inicio=2026-11-04T09:00:00-03:00 "
            "fim=2026-11-04T10:00:00-03:00 responsavel=Doc",
        )
        tarefa = corpo["result"]["task"]
        assert tarefa["status"]["state"] == "TASK_STATE_COMPLETED"
        artifact = tarefa["artifacts"][0]
        assert artifact["name"] == "reserva"
        conteudo = json.loads(artifact["parts"][0]["text"])
        assert conteudo["sala"] == "sala-porao"
        assert conteudo["politica"]

        # V26: GetTask reflete id, contextId e estado corrente.
        resposta_get = cliente.post(
            "/a2a",
            json={"jsonrpc": "2.0", "id": 2, "method": "GetTask", "params": {"id": tarefa["id"]}},
        )
        # a2a-sdk==1.2.2 não tem GetTaskResponse: devolve o Task cru em `result`
        # (ver DESAFIOS.md), tal como o próprio validador já contempla.
        obtida = resposta_get.json()["result"]
        assert obtida["id"] == tarefa["id"]
        assert obtida["contextId"] == tarefa["contextId"]
        assert obtida["status"]["state"] == "TASK_STATE_COMPLETED"

        # V31: SendMessage para Task terminal é recusado.
        recusada = _enviar(cliente, "escolha=sala-porao", task_id=tarefa["id"])
        assert "error" in recusada

        # V35: sala inexistente termina a Task em FAILED com a mensagem da tool.
        falhou = _enviar(
            cliente,
            "reservar sala=sala-delorean inicio=2026-11-04T09:00:00-03:00 "
            "fim=2026-11-04T10:00:00-03:00 responsavel=Doc",
        )
        tarefa_falha = falhou["result"]["task"]
        assert tarefa_falha["status"]["state"] == "TASK_STATE_FAILED"
        mensagem = tarefa_falha["status"]["message"]["parts"][0]["text"]
        assert "Sala inexistente: sala-delorean" in mensagem
        # A2A-08: mensagem exata visivel no status *e* no history da Task.
        mensagens_no_history = [p["text"] for m in tarefa_falha["history"] for p in m["parts"]]
        assert mensagem in mensagens_no_history
