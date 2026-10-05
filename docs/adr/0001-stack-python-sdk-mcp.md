# ADR-0001 — Python 3.12 com SDK oficial `mcp==2.3.0`

- **Status:** aceito · **Data:** 2026-10-05

## Contexto
O enunciado aceita Node (`@modelcontextprotocol/server`) ou Python (`mcp`), ambos na v2 alinhada à spec `2026-07-28`. Os exemplos de `exemplos/wire/` foram capturados com o SDK Python (chave `__main__:escolha_de_sala`, `requestState` prefixado `v1.`, schemas pydantic com `$defs`). O validador também é Python.

## Opções
1. **Python 3.12** — Prós: menor distância do wire de referência; MRTR, selagem e schemas saem do SDK na mesma forma; uma linguagem só no repo inteiro. Contras: tipagem estática opcional (mitigada com mypy).
2. **Node 20 + TS** — Prós: tipagem forte. Contras: divergências de forma a conferir (chave de `inputRequests`, `const` vs `enum`), etapa de build.

## Decisão
Python 3.12, `mcp==2.3.0`, `uvicorn` como servidor ASGI.

## Consequências
Seguir as docstrings do SDK para `input_required`; não tentar imitar o SDK Node.
