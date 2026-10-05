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

## Notas da fase 001-servidor-mcp
- **`_meta` obrigatório é 100% do SDK, sem middleware.** `classify_inbound_request` (`mcp.shared.inbound`) roda *antes* do dispatcher/middleware, numa ladder: `_meta` ausente ou sem `protocolVersion`/`clientCapabilities` → `INVALID_PARAMS` (-32602), mapeado para HTTP 400 por `ERROR_CODE_HTTP_STATUS`. Confirma MCP-01/V04/V05 sem nenhum código nosso.
- **Tool desconhecida** (`ToolManager.call_tool`) e **URI de resource inexistente** (`ResourceNotFoundError`) também já chegam prontos do SDK: a primeira como `isError: true` (satisfaz V06, que aceita -32602 *ou* isError), a segunda como -32602 automático (V08). Nenhum tratamento manual necessário.
- **`ToolError` preserva a mensagem como substring**, só prefixa com `"Error executing tool <nome>: "`. Os checks V09–V12 usam `in texto(...)`, então levantar `ToolError(str(erro_de_dominio))` no adapter basta — não precisa reconstruir `CallToolResult` à mão para manter a mensagem exata.
- **Resource estático não recebe `Context`** (`FunctionResource.fn: Callable[[], Any]`, só `ResourceTemplate` injeta `ctx`). Carregar `dados/` e a versão da política uma vez em `criar_app()` e capturar por closure resolve sem precisar do `lifespan` do `MCPServer`.
- **Nome da função decorada define o `title` do `inputSchema`** (`<nome_da_função>Arguments`), não o `name=` passado ao decorator — por isso as funções das tools têm o mesmo nome da tool (ex.: `def reservar_sala(...)`), e chamam a camada de `application` por acesso qualificado (`casos_de_uso.reservar_sala(...)`) para não colidir.

## Notas da fase 002-mrtr (investigação "input_required não sai")
- **Causa do V13–V19 falhando:** o `Elicit` só é interceptado quando devolvido por um *resolver injetado* num parâmetro `Annotated[..., Resolve(fn)]`. Chamar o resolver dentro do corpo da tool e devolver `Elicit` como retorno não aciona nada (o SDK serializa como resultado comum). Ver `mcp/server/mcpserver/resolve.py` (`resolve_arguments` roda **antes** do corpo; se há pendência, devolve `InputRequiredResult` e o corpo não executa).
- **`Elicit(message, schema)`: `schema` é uma classe pydantic, não um dict.** Para enum dinâmico: `create_model("EscolhaSala", sala=(Literal[tuple(alts)], Field(description=...)))` → renderiza exatamente o `requestedSchema` do wire 03 (`title: "Sala"`, `enum`, `required`).
- **Desenho:** resolver `escolha_de_sala(sala, inicio, fim)` (args pegos por nome; repo por closure) é **só leitura**: sem conflito → `None`; com conflito → `Elicit` com as alternativas. A tool recebe `escolha: Annotated[ElicitationResult[...], Resolve(escolha_de_sala)]` e só ela grava: `Accepted(data=None)` → reserva a sala pedida; `Accepted(data)` → reserva `data.sala`; `Declined`/`Cancelled` → `reservado=false, motivo="recusado"`. Nunca gravar dentro do resolver (ele reexecuta a cada rodada).
- **O enum precisa renderizar igual nas duas rodadas:** o SDK guarda o digest da pergunta no `requestState`; se as alternativas mudarem entre pausa e retry, a resposta é descartada e a pergunta é refeita (novo `input_required`) — resolve a pendência "sala ocupada entre pausa e retry" sem código extra.
- **Grátis do SDK (spike confirmado):** `-32021` sem capability (HTTP 400), escolha fora do enum → `isError`, `requestState` adulterado → `-32602` (motivo `seal`), argumentos adulterados → `-32602` (motivo `request binding`). O parâmetro resolvido não aparece no `inputSchema` do `tools/list`.
- **Chave de `inputRequests`** com closure: `"<módulo>:criar_app.<locals>.escolha_de_sala"` — difere do wire (`__main__:escolha_de_sala`), mas é opaca para o cliente (o agente lê a chave única de `inputRequests`).
- **Implementado (T2.2–T2.5):** `casos_de_uso.verificar_conflito_reserva` (consulta) separado de `casos_de_uso.reservar_sala` (gravação); `adapters/mcp/mrtr.py` tem o resolver; `adapters/mcp/server.py` conecta via `Resolve`. `rodar-validador`: V13–V20 verdes.
- **`from __future__ import annotations` quebra `Annotated[T, Resolve(fn)]` com `fn` de variável local.** O módulo do adapter tem a future import (PEP 563: anotações viram string); `fn.__globals__` não inclui o escopo de `criar_app`, então `inspect.signature(fn, eval_str=True)` (usado pelo SDK para montar o `inputSchema`) levanta `InvalidSignature: Unable to evaluate type annotations`. Contorno: definir a tool sem anotar `escolha` na assinatura, atribuir `reservar_sala.__annotations__ = {...}` com os objetos reais (não strings) e registrar com `servidor.tool(...)(reservar_sala)` em vez de `@servidor.tool(...)` (o decorator correria antes do patch). Ver `DESAFIOS.md`.

## Pendências
~~Comportamento quando a sala escolhida foi ocupada entre pausa e retry — não implementado.~~
Verificado (retroativo, fora da fase 2 original): é coberto de graça pelo mecanismo da nota da linha 32 — o resolver reexecuta no retry, recalcula as alternativas, e se a escolha enviada não está mais entre elas o SDK descarta a resposta ("the question changed since it was asked") e devolve uma nova pausa com as alternativas atuais; `casos_de_uso.reservar_sala` nunca chega a gravar a sala obsoleta. Teste de regressão: `test_mrtr_alternativa_tomada_entre_pausa_e_retry_gera_nova_pausa` em `servidor-mcp/tests/integration/test_app.py`.
