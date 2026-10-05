"""Script de fumaça (ENUNCIADO, passo 6): cliente MCP puro, sem A2A.

Descobre as tools, lê a política, e completa o ciclo de MRTR respondendo a
elicitation na mão (escolha fixa, sem pedir input ao usuário). Espera um
servidor MCP recém-iniciado (ver DESAFIOS.md): reservas de uma execução
conflitam com a seguinte.

Uso: ``uv run --package agente python -m agente_salas.smoke`` com o servidor
MCP já de pé em ``MCP_URL`` (padrão http://127.0.0.1:7301/mcp).
"""

from __future__ import annotations

import asyncio
import os
import sys

from agente_salas.adapters.mcp_client.cliente import ClienteSalas
from agente_salas.domain.pendencia import ArgsReserva, RespostaElicitation
from agente_salas.domain.resultados import Concluido, Falhou, PrecisaEntrada, Recusado
from agente_salas.domain.trace import iniciar
from agente_salas.infra.config import ErroConfig, carregar_config

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


async def executar(mcp_url: str) -> None:
    trace = iniciar(None)
    print(f"traceparent desta execucao: {trace.traceparent}")
    print("procure esse valor no stderr do servidor MCP para conferir a propagacao.\n")

    async with ClienteSalas(mcp_url) as cliente:
        await cliente.descobrir()
        print("descoberta ok: reservar_sala encontrada em tools/list")

        versao = await cliente.versao_politica(trace.com_novo_span())
        print(f"politica de uso: versao {versao}")

        print(f"\n1) reservando em intervalo livre: {ARGS_LIVRE.sala}")
        _imprimir(await cliente.reservar(ARGS_LIVRE, trace.com_novo_span()))

        print(f"\n2) reservando em intervalo com conflito: {ARGS_CONFLITO.sala}")
        pausado = await cliente.reservar(ARGS_CONFLITO, trace.com_novo_span())
        _imprimir(pausado)
        if not isinstance(pausado, PrecisaEntrada):
            return

        escolhida = pausado.pendencia.alternativas[0]
        print(f"\n3) retomando (id JSON-RPC novo) escolhendo alternativa: {escolhida}")
        resposta = RespostaElicitation(acao="accept", sala=escolhida)
        resultado = await cliente.retomar(
            ARGS_CONFLITO, pausado.pendencia, resposta, trace.com_novo_span()
        )
        _imprimir(resultado)


def _imprimir(resultado: Concluido | Falhou | Recusado | PrecisaEntrada) -> None:
    match resultado:
        case Concluido():
            print(f"   concluido: reserva={resultado.reserva} sala={resultado.sala}")
        case Falhou():
            print(f"   falhou: {resultado.mensagem}")
        case Recusado():
            print(f"   recusado: motivo={resultado.motivo}")
        case PrecisaEntrada():
            alternativas = resultado.pendencia.alternativas
            print(f"   precisa entrada: {resultado.mensagem} alternativas={alternativas}")


def main() -> None:
    try:
        config = carregar_config(os.environ)
    except ErroConfig as erro:
        print(f"Configuração inválida: {erro}", file=sys.stderr)
        sys.exit(1)
    asyncio.run(executar(config.mcp_url))


if __name__ == "__main__":
    main()
