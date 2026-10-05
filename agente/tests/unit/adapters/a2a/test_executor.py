import json

from starlette.testclient import TestClient

from agente_salas.adapters.a2a.app import criar_app
from agente_salas.infra.config import ConfigAgente

from ..mcp_client.fake_servidor import SALA_INEXISTENTE, SALA_OCUPADA, criar_servidor_fake

CONFIG = ConfigAgente(porta=7300, mcp_url="http://unused")


def _enviar(cliente: TestClient, texto: str, task_id: str | None = None) -> dict:
    params: dict = {"message": {"messageId": "m1", "role": "ROLE_USER", "parts": [{"text": texto}]}}
    if task_id:
        params["message"]["taskId"] = task_id
    resposta = cliente.post(
        "/a2a", json={"jsonrpc": "2.0", "id": 1, "method": "SendMessage", "params": params}
    )
    assert resposta.status_code == 200
    return resposta.json()


def test_pedido_em_sala_livre_conclui_a_task() -> None:
    app = criar_app(CONFIG, servidor_mcp=criar_servidor_fake())
    with TestClient(app) as cliente:
        corpo = _enviar(
            cliente,
            "reservar sala=sala-aquario inicio=2026-11-03T09:00:00-03:00 "
            "fim=2026-11-03T10:00:00-03:00 responsavel=Doc",
        )
    tarefa = corpo["result"]["task"]
    assert tarefa["status"]["state"] == "TASK_STATE_COMPLETED"
    artifact = tarefa["artifacts"][0]
    assert artifact["name"] == "reserva"
    conteudo = json.loads(artifact["parts"][0]["text"])
    assert conteudo["sala"] == "sala-aquario"
    assert conteudo["reserva"] == "res-0001"


def test_sala_inexistente_termina_a_task_em_failed() -> None:
    app = criar_app(CONFIG, servidor_mcp=criar_servidor_fake())
    with TestClient(app) as cliente:
        corpo = _enviar(
            cliente,
            f"reservar sala={SALA_INEXISTENTE} inicio=2026-11-03T09:00:00-03:00 "
            "fim=2026-11-03T10:00:00-03:00 responsavel=Doc",
        )
    tarefa = corpo["result"]["task"]
    assert tarefa["status"]["state"] == "TASK_STATE_FAILED"
    mensagem_status = tarefa["status"]["message"]["parts"][0]["text"]
    assert f"Sala inexistente: {SALA_INEXISTENTE}" in mensagem_status
    # A2A-08: a mensagem de erro tem que aparecer no status *e* no history.
    mensagens_no_history = [p["text"] for m in tarefa["history"] for p in m["parts"]]
    assert mensagem_status in mensagens_no_history


def test_comando_malformado_termina_a_task_em_failed() -> None:
    app = criar_app(CONFIG, servidor_mcp=criar_servidor_fake())
    with TestClient(app) as cliente:
        corpo = _enviar(cliente, "oi tudo bem")
    tarefa = corpo["result"]["task"]
    assert tarefa["status"]["state"] == "TASK_STATE_FAILED"


def test_send_message_em_task_terminal_e_recusado() -> None:
    app = criar_app(CONFIG, servidor_mcp=criar_servidor_fake())
    with TestClient(app) as cliente:
        primeiro = _enviar(
            cliente,
            "reservar sala=sala-aquario inicio=2026-11-03T09:00:00-03:00 "
            "fim=2026-11-03T10:00:00-03:00 responsavel=Doc",
        )
        task_id = primeiro["result"]["task"]["id"]
        segundo = _enviar(cliente, "escolha=sala-fusca", task_id=task_id)
    assert "error" in segundo


def test_get_task_reflete_estado_corrente() -> None:
    app = criar_app(CONFIG, servidor_mcp=criar_servidor_fake())
    with TestClient(app) as cliente:
        enviado = _enviar(
            cliente,
            "reservar sala=sala-aquario inicio=2026-11-03T09:00:00-03:00 "
            "fim=2026-11-03T10:00:00-03:00 responsavel=Doc",
        )
        task_id = enviado["result"]["task"]["id"]
        resposta = cliente.post(
            "/a2a",
            json={"jsonrpc": "2.0", "id": 2, "method": "GetTask", "params": {"id": task_id}},
        )
    # a2a-sdk==1.2.2 não tem `GetTaskResponse`/wrapper "task" (ver DESAFIOS.md);
    # devolve o `Task` direto em `result`, como o próprio validador já contempla.
    tarefa = resposta.json()["result"]
    assert tarefa["id"] == task_id
    assert tarefa["contextId"]
    assert tarefa["status"]["state"] == "TASK_STATE_COMPLETED"


PEDIDO_OCUPADO = (
    f"reservar sala={SALA_OCUPADA} inicio=2026-11-03T14:00:00-03:00 "
    "fim=2026-11-03T15:00:00-03:00 responsavel=Marty"
)
LINHA_PAUSA = "alternativas: sala-fusca, sala-mirante"


def _status(corpo: dict) -> tuple[str, str]:
    tarefa = corpo["result"]["task"]
    partes = (tarefa["status"].get("message") or {}).get("parts") or []
    return tarefa["status"]["state"], " ".join(p.get("text", "") for p in partes)


def test_sala_ocupada_pausa_a_task_com_as_alternativas() -> None:
    app = criar_app(CONFIG, servidor_mcp=criar_servidor_fake())
    with TestClient(app) as cliente:
        corpo = _enviar(cliente, PEDIDO_OCUPADO)
    assert _status(corpo) == ("TASK_STATE_INPUT_REQUIRED", LINHA_PAUSA)


def test_escolha_invalida_mantem_pausa_e_valida_conclui_na_sala_escolhida() -> None:
    app = criar_app(CONFIG, servidor_mcp=criar_servidor_fake())
    with TestClient(app) as cliente:
        task_id = _enviar(cliente, PEDIDO_OCUPADO)["result"]["task"]["id"]
        invalida = _enviar(cliente, "escolha=sala-aquario", task_id=task_id)
        valida = _enviar(cliente, "escolha=sala-fusca", task_id=task_id)
        terminal = _enviar(cliente, "escolha=sala-mirante", task_id=task_id)

    assert _status(invalida) == ("TASK_STATE_INPUT_REQUIRED", LINHA_PAUSA)
    tarefa = valida["result"]["task"]
    assert tarefa["id"] == task_id
    assert tarefa["status"]["state"] == "TASK_STATE_COMPLETED"
    assert json.loads(tarefa["artifacts"][0]["parts"][0]["text"])["sala"] == "sala-fusca"
    assert "error" in terminal


def test_recusar_termina_a_task_em_canceled() -> None:
    app = criar_app(CONFIG, servidor_mcp=criar_servidor_fake())
    with TestClient(app) as cliente:
        task_id = _enviar(cliente, PEDIDO_OCUPADO)["result"]["task"]["id"]
        corpo = _enviar(cliente, "escolha=recusar", task_id=task_id)
    estado, _ = _status(corpo)
    assert estado == "TASK_STATE_CANCELED"
