"""T3.6: `ClienteSalas` contra um servidor MCP real, em subprocesso.

Confere no stderr do servidor (AV5/AV6): `tools/list` antes do primeiro
`tools/call`, o mesmo trace-id propagado em toda chamada da Task, e um id
JSON-RPC novo a cada `tools/call` (inicial e retry, HOST-07).
"""

from __future__ import annotations

import os
import secrets
import socket
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from agente_salas.adapters.mcp_client.cliente import ClienteSalas
from agente_salas.adapters.mcp_client.trace import iniciar
from agente_salas.domain.pendencia import ArgsReserva, RespostaElicitation
from agente_salas.domain.resultados import Concluido, PrecisaEntrada

RAIZ = Path(__file__).resolve().parents[3]
PORTA = 7391

ARGS_LIVRE = ArgsReserva(
    sala="sala-aquario",
    inicio="2026-11-03T09:00:00-03:00",
    fim="2026-11-03T10:00:00-03:00",
    responsavel="Doc",
)
ARGS_CONFLITO = ArgsReserva(
    sala="sala-garagem",
    inicio="2026-11-03T14:00:00-03:00",
    fim="2026-11-03T15:00:00-03:00",
    responsavel="Marty",
)


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
def log_servidor_mcp(tmp_path: Path) -> Iterator[Path]:
    log = tmp_path / "mcp.log"
    ambiente = {**os.environ, "REQUEST_STATE_SECRET": secrets.token_hex(32), "MCP_PORT": str(PORTA)}
    with log.open("w") as arquivo_log:
        processo = subprocess.Popen(
            ["uv", "run", "--package", "servidor-mcp", "python", "-m", "central_salas"],
            cwd=RAIZ,
            env=ambiente,
            stdout=subprocess.DEVNULL,
            stderr=arquivo_log,
        )
    try:
        _esperar_porta(PORTA)
        yield log
    finally:
        processo.terminate()
        try:
            processo.wait(timeout=10)
        except subprocess.TimeoutExpired:
            processo.kill()
            processo.wait(timeout=10)


async def test_tools_list_antes_de_tools_call_e_traceparent_propagado(
    log_servidor_mcp: Path,
) -> None:
    trace = iniciar(None)

    async with ClienteSalas(f"http://127.0.0.1:{PORTA}/mcp") as cliente:
        await cliente.descobrir()

        resultado_livre = await cliente.reservar(ARGS_LIVRE, trace.com_novo_span())
        assert isinstance(resultado_livre, Concluido)

        pausado = await cliente.reservar(ARGS_CONFLITO, trace.com_novo_span())
        assert isinstance(pausado, PrecisaEntrada)

        escolhida = pausado.pendencia.alternativas[0]
        resposta = RespostaElicitation(acao="accept", sala=escolhida)
        final = await cliente.retomar(
            ARGS_CONFLITO, pausado.pendencia, resposta, trace.com_novo_span()
        )
        assert isinstance(final, Concluido)
        assert final.sala == escolhida

    linhas = [
        linha for linha in log_servidor_mcp.read_text().splitlines() if linha.startswith("method=")
    ]

    indice_list = next(i for i, linha in enumerate(linhas) if "method=tools/list" in linha)
    indice_primeiro_call = next(i for i, linha in enumerate(linhas) if "method=tools/call" in linha)
    assert indice_list < indice_primeiro_call, "tools/list deve vir antes do 1º tools/call (AV5)"

    linhas_com_trace = [linha for linha in linhas if trace.trace_id in linha]
    assert len(linhas_com_trace) >= 3, (
        "o trace-id da Task deve propagar em reservar/retomar (HOST-04)"
    )

    ids_dos_calls = [
        linha.split(" id=")[1].split(" ")[0] for linha in linhas if "method=tools/call" in linha
    ]
    assert len(ids_dos_calls) == len(set(ids_dos_calls)), (
        "cada tools/call (inicial e retry) precisa de um id JSON-RPC novo (HOST-07)"
    )
