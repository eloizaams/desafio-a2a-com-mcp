# ADR-0003 — Cliente MCP do agente

- **Status:** proposto (decidido pelo spike T0.4) · **Data:** 2026-10-05

## Contexto
O agente precisa ver o `input_required` **cru** para pausar a Task. O enunciado avisa: o cliente do SDK com callback de elicitation responde sozinho e a Task nunca pausa. Também precisa de id novo no retry, `_meta.traceparent` por request e headers `Mcp-Method`/`Mcp-Name`.

## Opções
1. **`ClientSession` do SDK, sem callback** — Prós: cliente "de verdade", headers/_meta do transporte gerados pelo SDK. Contras: risco de não expor o resultado cru ou de controlar id.
2. **Cliente fino com `httpx`** — Prós: controle total, ~100 linhas, fácil de testar. Contras: reimplementa parte do transporte.

## Critérios do spike
(a) `input_required` cru acessível; (b) `_meta` por request; (c) headers espelhados; (d) id novo no retry. Todos sim → opção 1. Algum não → opção 2, com a evidência copiada aqui.

## Decisão
_pendente_
