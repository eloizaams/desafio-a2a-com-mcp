"""T4.6/T5.5: o app A2A do agente contra um servidor MCP real, em subprocesso.

Espelha os checks V24-V33, V35 e V36 do validador (caminho feliz, GetTask,
pausa MRTR e retomada, recusa, Tasks pausadas em paralelo, Task terminal
recusa SendMessage, sala inexistente -> FAILED, pausa determinística), e
confere no stderr do MCP o trace-id da Task e o id novo no retry.
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
def log_mcp(tmp_path: Path) -> Path:
    return tmp_path / "mcp.log"


@pytest.fixture
def servidor_mcp_real(log_mcp: Path) -> Iterator[str]:
    ambiente = {
        **os.environ,
        "REQUEST_STATE_SECRET": secrets.token_hex(32),
        "MCP_PORT": str(PORTA_MCP),
    }
    with log_mcp.open("w") as arquivo_log:
        processo = subprocess.Popen(
            ["uv", "run", "--package", "servidor-mcp", "python", "-m", "central_salas"],
            cwd=RAIZ,
            env=ambiente,
            stdout=subprocess.DEVNULL,
            stderr=arquivo_log,
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


def _enviar(
    cliente: TestClient, texto: str, task_id: str | None = None, traceparent: str | None = None
) -> dict:
    mensagem: dict = {"messageId": "m1", "role": "ROLE_USER", "parts": [{"text": texto}]}
    if task_id:
        mensagem["taskId"] = task_id
    resposta = cliente.post(
        "/a2a",
        json={"jsonrpc": "2.0", "id": 1, "method": "SendMessage", "params": {"message": mensagem}},
        headers={"traceparent": traceparent} if traceparent else {},
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


def _h(hora: str) -> str:
    return f"2026-11-03T{hora}:00-03:00"


def _estado(corpo: dict) -> str:
    return corpo["result"]["task"]["status"]["state"]


def _mensagem(corpo: dict) -> str:
    partes = (corpo["result"]["task"]["status"].get("message") or {}).get("parts") or []
    return " ".join(p.get("text", "") for p in partes)


def _reserva(corpo: dict) -> dict:
    return json.loads(corpo["result"]["task"]["artifacts"][0]["parts"][0]["text"])


def _linhas_log(log: Path) -> list[str]:
    return [linha for linha in log.read_text().splitlines() if linha.startswith("method=")]


def test_ponte_mrtr_contra_mcp_real(servidor_mcp_real: str, log_mcp: Path) -> None:
    app = criar_app(ConfigAgente(porta=7300, mcp_url=servidor_mcp_real))
    trace_id = secrets.token_hex(16)
    traceparent = f"00-{trace_id}-{secrets.token_hex(8)}-01"
    ocupado = f"reservar sala=sala-garagem inicio={_h('14:00')} fim={_h('15:00')} responsavel=Marty"

    with TestClient(app) as cliente:
        # V27, V28: sala ocupada pausa a Task com as alternativas na ordem.
        pausada = _enviar(cliente, ocupado, traceparent=traceparent)
        assert _estado(pausada) == "TASK_STATE_INPUT_REQUIRED"
        assert _mensagem(pausada) == "alternativas: sala-fusca, sala-mirante"
        task_id = pausada["result"]["task"]["id"]

        # V29: escolha fora do enum mantém a pausa (sem tools/call novo).
        chamadas_antes = len([x for x in _linhas_log(log_mcp) if "tools/call" in x])
        invalida = _enviar(cliente, "escolha=sala-aquario", task_id=task_id)
        assert _estado(invalida) == "TASK_STATE_INPUT_REQUIRED"
        assert len([x for x in _linhas_log(log_mcp) if "tools/call" in x]) == chamadas_antes

        # V30: escolha válida conclui na sala escolhida.
        concluida = _enviar(cliente, "escolha=sala-fusca", task_id=task_id)
        assert _estado(concluida) == "TASK_STATE_COMPLETED"
        assert _reserva(concluida)["sala"] == "sala-fusca"

        # V31: Task terminal recusa nova mensagem.
        assert "error" in _enviar(cliente, "escolha=sala-mirante", task_id=task_id)

        # V32: recusa termina em CANCELED.
        recusavel = _enviar(
            cliente,
            f"reservar sala=sala-garagem inicio={_h('14:30')} fim={_h('15:30')} responsavel=Biff",
        )
        recusa = _enviar(cliente, "escolha=recusar", task_id=recusavel["result"]["task"]["id"])
        assert _estado(recusa) == "TASK_STATE_CANCELED"

        # V33: duas Tasks pausadas ao mesmo tempo, cada uma com seu requestState.
        a = _enviar(
            cliente,
            f"reservar sala=sala-fusca inicio={_h('16:00')} fim={_h('17:00')} responsavel=Lorraine",
        )
        b = _enviar(
            cliente,
            f"reservar sala=sala-garagem inicio={_h('14:00')} fim={_h('15:00')} responsavel=George",
        )
        assert _estado(a) == _estado(b) == "TASK_STATE_INPUT_REQUIRED"
        fim_a = _enviar(cliente, "escolha=sala-mirante", task_id=a["result"]["task"]["id"])
        fim_b = _enviar(cliente, "escolha=sala-mirante", task_id=b["result"]["task"]["id"])
        assert _estado(fim_a) == _estado(fim_b) == "TASK_STATE_COMPLETED"
        assert _reserva(fim_a)["reserva"] != _reserva(fim_b)["reserva"]
        assert _reserva(fim_a)["inicio"] != _reserva(fim_b)["inicio"]

        # V36: o mesmo pedido em conflito produz a mesma pausa, byte a byte.
        livre = f"reservar sala=sala-porao inicio={_h('09:00')} fim={_h('10:00')} responsavel=Doc"
        assert _estado(_enviar(cliente, livre)) == "TASK_STATE_COMPLETED"
        repetido = livre
        m1, m2 = _mensagem(_enviar(cliente, repetido)), _mensagem(_enviar(cliente, repetido))
        assert m1 == m2
        assert m1.startswith("alternativas:")

    linhas = _linhas_log(log_mcp)
    # AV5: descoberta antes do 1º tools/call.
    primeiro_list = next(i for i, x in enumerate(linhas) if "method=tools/list" in x)
    primeiro_call = next(i for i, x in enumerate(linhas) if "method=tools/call" in x)
    assert primeiro_list < primeiro_call
    # AV7/HOST-04: pausa e retry da 1ª Task levam o trace-id recebido no SendMessage.
    calls_da_task = [x for x in linhas if "method=tools/call" in x and trace_id in x]
    assert len(calls_da_task) == 2
    # HOST-07: retry com id JSON-RPC novo.
    ids = [x.split(" id=")[1].split(" ")[0] for x in calls_da_task]
    assert ids[0] != ids[1]
