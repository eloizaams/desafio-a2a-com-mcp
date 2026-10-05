#!/usr/bin/env python3
"""Reenvia o request de um exemplos/wire/NN-*.json ao processo local e mostra o diff estrutural.

    python3 scripts/conferir_wire.py 03
    python3 scripts/conferir_wire.py 03 --request-state v1.xxx   # para passos de retry

Ignora valores voláteis (ids gerados, requestState, timestamps). Biblioteca padrão apenas.
Lembre: reservas criadas mudam o estado; reinicie os processos entre comparações de conflito.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

PASTA_WIRE = Path(__file__).resolve().parent.parent / "exemplos" / "wire"
CHAVES_VOLATEIS = {
    "requestState",
    "id",
    "taskId",
    "contextId",
    "messageId",
    "artifactId",
    "timestamp",
}
LARGURA_VALOR = 60
CABECALHOS_PROIBIDOS = {"content-length", "host"}


def carregar_exemplo(numero: str) -> dict[str, Any]:
    candidatos = sorted(PASTA_WIRE.glob(f"{numero.zfill(2)}-*.json"))
    if not candidatos:
        sys.exit(f"Nenhum exemplo {numero} em {PASTA_WIRE}")
    return json.loads(candidatos[0].read_text())


def enviar(request: dict[str, Any]) -> tuple[int, Any]:
    corpo = request.get("body")
    dados = json.dumps(corpo).encode() if corpo is not None else None
    cabecalhos = {
        k: v for k, v in request.get("headers", {}).items() if k.lower() not in CABECALHOS_PROIBIDOS
    }
    req = urllib.request.Request(
        request["url"], data=dados, headers=cabecalhos, method=request.get("metodo", "POST")
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resposta:
            return resposta.status, json.loads(resposta.read() or b"null")
    except urllib.error.HTTPError as erro:
        return erro.code, json.loads(erro.read() or b"null")


def diff(esperado: Any, obtido: Any, caminho: str = "$") -> list[str]:
    if isinstance(esperado, dict) and isinstance(obtido, dict):
        linhas = []
        for chave in sorted(set(esperado) | set(obtido)):
            sub = f"{caminho}.{chave}"
            if chave not in obtido:
                linhas.append(f"- faltando  {sub}")
            elif chave not in esperado:
                linhas.append(f"+ sobrando  {sub} = {json.dumps(obtido[chave])[:LARGURA_VALOR]}")
            elif chave not in CHAVES_VOLATEIS:
                linhas += diff(esperado[chave], obtido[chave], sub)
        return linhas
    if isinstance(esperado, list) and isinstance(obtido, list):
        if len(esperado) != len(obtido):
            return [f"~ tamanho   {caminho}: esperado {len(esperado)}, obtido {len(obtido)}"]
        return [
            linha
            for i, (e, o) in enumerate(zip(esperado, obtido, strict=True))
            for linha in diff(e, o, f"{caminho}[{i}]")
        ]
    if esperado != obtido:
        e, o = json.dumps(esperado)[:LARGURA_VALOR], json.dumps(obtido)[:LARGURA_VALOR]
        return [f"~ valor     {caminho}: esperado {e}, obtido {o}"]
    return []


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("numero", help="número do exemplo, ex.: 03")
    parser.add_argument(
        "--request-state", help="substitui params.requestState do request (passos de retry)"
    )
    args = parser.parse_args()

    exemplo = carregar_exemplo(args.numero)
    request = exemplo["request"]
    if args.request_state:
        request["body"]["params"]["requestState"] = args.request_state
    status, corpo = enviar(request)
    esperado = exemplo["response"]

    print(f"# {exemplo.get('descricao', '')}")
    print(f"HTTP esperado {esperado.get('httpStatus')}, obtido {status}")
    linhas = diff(esperado.get("body"), corpo)
    print("\n".join(linhas) if linhas else "Corpo estruturalmente igual (ignorando voláteis).")
    sys.exit(1 if linhas or status != esperado.get("httpStatus") else 0)


if __name__ == "__main__":
    main()
