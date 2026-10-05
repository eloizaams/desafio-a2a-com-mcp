# ADR-0006 — Proteção e conteúdo do `requestState`

- **Status:** aceito (API confirmada no spike T0.5) · **Data:** 2026-10-05

## Decisão
- Selagem com o utilitário do SDK: `RequestStateSecurity(keys=[REQUEST_STATE_SECRET], ttl=600)` passado em `MCPServer(request_state_security=…)`. AES-256-GCM (chave via HKDF-SHA256), token `v1.` — **cifrado**, não só assinado.
- Chave: `REQUEST_STATE_SECRET` (hex de 32 bytes, `secrets.token_hex(32)`); servidor não sobe sem ela (o próprio codec rejeita < 32 bytes).
- TTL: **10 minutos** (dentro de 5–30; tempo razoável para humano responder sem janela longa de replay).
- Nada em memória entre `input_required` e retry ⇒ sobrevive a restart (confirmado no spike: token emitido antes do restart concluiu o retry depois).

## Notas do spike T0.5 (`mcp==2.3.0`)
- **MRTR no servidor:** parâmetro da tool `Annotated[ElicitationResult[T], Resolve(fn)]`; o resolver `fn` devolve `Elicit(mensagem, Schema)` quando precisa perguntar. Em `>= 2026-07-28` o SDK responde `resultType: "input_required"` com `inputRequests` cuja chave é `"<módulo>:<qualname>"` (daí `__main__:escolha_de_sala` no wire). `Literal[...]` no schema vira `enum`. Recusa chega como `DeclinedElicitation`.
- **-32021:** automático (`resolve._require_capability`) com `data.requiredCapabilities = {elicitation: {form: {}}}` e HTTP 400 — bate com V15.
- **Selagem/verificação:** `RequestStateBoundary` (instalado pelo `MCPServer`) sela na saída e verifica na entrada. O envelope vincula método, nome da tool, **digest dos argumentos**, audiência (nome do servidor) e expiração. Falha → `-32602 "Invalid or expired requestState"` (HTTP 400), motivo real só no log (`seal`, `request binding`, `expired`).
- **V18 (argumentos adulterados):** coberto pelo vínculo de argumentos do SDK → erro `-32602` (o validador aceita erro *ou* valores selados vencendo). Não é preciso selar `sala/inicio/fim/responsavel` manualmente.
- **Conteúdo do estado:** o SDK guarda só as respostas já obtidas; o resolver é reexecutado a cada rodada. Alternativas devem ser recalculadas de forma determinística no retry e a escolha validada contra elas.
- **Stateless:** `mcp.streamable_http_app(stateless_http=True, json_response=True)`, path `/mcp`.
- **Middleware:** `MCPServer(middleware=[fn])`, `fn(ctx, call_next)`; `ctx.method`, `ctx.request_id`, `ctx.params["_meta"]["traceparent"]` disponíveis → log em stderr (MCP-xx).
- **`serverInfo.version`:** sai vazio por padrão → passar a versão ao `MCPServer` (fase 1).

## Pendências
Comportamento quando a sala escolhida foi ocupada entre pausa e retry (fase 2). Conferir se a validação de `_meta` obrigatório (-32602/400) já é do SDK ou precisa de middleware (fase 1).
