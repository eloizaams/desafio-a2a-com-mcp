# ADR-0003 — Cliente MCP do agente

- **Status:** aceito (spike T0.4, 2026-10-05) · **Data:** 2026-10-05

## Contexto
O agente precisa ver o `input_required` **cru** para pausar a Task. O enunciado avisa: o cliente do SDK com callback de elicitation responde sozinho e a Task nunca pausa. Também precisa de id novo no retry, `_meta.traceparent` por request e headers `Mcp-Method`/`Mcp-Name`.

## Opções
1. **`ClientSession` do SDK, sem callback** — Prós: cliente "de verdade", headers/_meta do transporte gerados pelo SDK. Contras: risco de não expor o resultado cru ou de controlar id.
2. **Cliente fino com `httpx`** — Prós: controle total, ~100 linhas, fácil de testar. Contras: reimplementa parte do transporte.

## Critérios do spike
(a) `input_required` cru acessível; (b) `_meta` por request; (c) headers espelhados; (d) id novo no retry. Todos sim → opção 1. Algum não → opção 2, com a evidência copiada aqui.

## Resultado do spike (mcp==2.3.0)
Servidor mínimo `MCPServer` + cliente `mcp.Client(transport, mode="2026-07-28")`, requests capturados por event hook do httpx.

| Critério | Resultado | Evidência |
|----------|-----------|-----------|
| (a) `input_required` cru | **sim** | `session.call_tool(..., allow_input_required=True)` devolve `InputRequiredResult` (com `input_requests` e `request_state`) sem rodar o driver de retry (`mcp/client/session.py`: overload `allow_input_required: bool`; driver em `mcp/client/_input_required.py` só roda pelo `Client.call_tool`). |
| (b) `_meta` por request | **sim** | `call_tool(..., meta={"traceparent": tp})`; o stamp (`_make_modern_stamp`, `session.py`) só acrescenta `protocolVersion`/`clientInfo`/`clientCapabilities` e preserva `traceparent`. Capturado: `"meta": {"traceparent": "00-4bf9…-01", "io.modelcontextprotocol/protocolVersion": "2026-07-28", …}`. |
| (c) headers | **sim** | Capturado: `mcp-protocol-version: 2026-07-28`, `mcp-method: tools/call`, `mcp-name: reservar_sala`. |
| (d) id novo no retry | **sim** | `JSONRPCDispatcher._next_id` monotônico; capturado `tools/list id=1`, `tools/call id=2`, retry `id=3`. |

## Decisão
**Opção 1.** `mcp.Client(<transporte streamable HTTP>, mode="2026-07-28", client_info=…)` e chamadas via `client.session.*` com `allow_input_required=True`. Nunca usar `Client.call_tool` (ele roda o driver e fecha o MRTR sozinho).

## Consequências / armadilhas
- A capability `elicitation` só é anunciada se houver `elicitation_callback` diferente do default (`session.py:635`). Passar um callback-guarda que **levanta erro** — com `allow_input_required=True` ele nunca é chamado; se for, é bug.
- O SDK anuncia `elicitation: {form: {}, url: {}}` (o wire de referência mostra só `form`); o servidor aceita os dois.
- `mode="2026-07-28"` adota a versão direto, sem `server/discover` — nenhum request extra antes do `tools/list`.
- O agente passa a depender de `mcp==2.3.0`; `httpx` direto deixa de ser necessário em runtime.
- **Um `Client` por processo, não por Task (achado da fase 005).** O id JSON-RPC é monotônico *por instância* de `Client`; na fase 004 cada Task abria um `ClienteSalas` novo, então o retry MRTR saía com `id=1`, igual à chamada pausada (HOST-07 violado, invisível ao validador, visível no stderr do MCP). Além disso o SDK só faz `tools/list` *depois* do 1º `tools/call` (para validar output schema) — AV5 exige o contrário. Correção: um único `ClienteSalas` aberto no lifespan do app A2A, com descoberta lazy antes do 1º `tools/call` (`_descoberto`).
