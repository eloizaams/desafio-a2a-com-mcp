# A Ponte: um agente A2A com MCP por dentro

Entrega do desafio MBA (Engenharia de Software com IA, curso de MCP e A2A). Dois processos Python 3.12, sem LLM no caminho de execução:

- **`servidor-mcp`** (`:7301`) — Streamable HTTP, três tools e um resource para a Central de Salas da Hill Valley Tech, com o ciclo MRTR completo em `reservar_sala`.
- **`agente`** (`:7300`) — host MCP por dentro, servidor A2A v1.0 por fora. É ele quem costura a ponte entre o `input_required` do MCP e a Task do A2A.

O enunciado completo está em [`docs/specs/ENUNCIADO.md`](docs/specs/ENUNCIADO.md); as decisões de projeto (SDD) em [`docs/specs/PLANO.md`](docs/specs/PLANO.md), [`docs/specs/constitution.md`](docs/specs/constitution.md) e [`docs/adr/`](docs/adr/).

## Como rodar

Requer [`uv`](https://docs.astral.sh/uv/) e Python 3.12.

```bash
git clone <url-do-seu-fork> desafio-a2a-com-mcp
cd desafio-a2a-com-mcp
uv sync

# gere o segredo do requestState (32+ bytes) e exporte — nunca comite o valor
python3 -c "import secrets; print(secrets.token_hex(32))"
export REQUEST_STATE_SECRET="<cole o valor gerado>"
```

Em dois terminais separados (cada um herda `REQUEST_STATE_SECRET` do ambiente):

```bash
# terminal 1 — servidor MCP, :7301, stderr com method/id/traceparent de cada request
uv run --package servidor-mcp python -m central_salas

# terminal 2 — agente A2A + host MCP, :7300
uv run --package agente python -m agente_salas
```

Com os dois no ar, rode o validador oficial do starter:

```bash
python3 validador/validar.py --agente http://localhost:7300 --mcp http://localhost:7301
```

Atalhos equivalentes em `scripts/` (`subir-mcp.sh`, `subir-agente.sh`, lêem `.env` da raiz se existir) e a skill interna `rodar-validador` (mata o que estiver nas portas, sobe os dois com um segredo temporário, roda o validador e confirma o `traceparent` no log — usada durante o desenvolvimento, não é necessária para a entrega).

## Onde a ponte acontece

**Ida — `input_required` do MCP vira pausa da Task:**
1. O cliente MCP do agente (`ClienteSalas._chamar_reservar_sala`, [`agente/src/agente_salas/adapters/mcp_client/cliente.py:133`](agente/src/agente_salas/adapters/mcp_client/cliente.py#L133)) chama `reservar_sala` com `allow_input_required=True` e recebe o `InputRequiredResult` cru, sem fechar o ciclo sozinho.
2. `Ponte._desfecho` ([`agente/src/agente_salas/application/ponte.py:92`](agente/src/agente_salas/application/ponte.py#L92)) detecta um `PrecisaEntrada`, guarda a `PendenciaMRTR` (chave, `requestState` opaco, alternativas, args originais, trace) indexada por `task_id` em `Pendencias` ([`agente/src/agente_salas/application/pendencias.py:20`](agente/src/agente_salas/application/pendencias.py#L20), só em memória do processo do agente) e devolve um `Pausado`.
3. O executor A2A ([`agente/src/agente_salas/adapters/a2a/executor.py:58`](agente/src/agente_salas/adapters/a2a/executor.py#L58)) traduz `Pausado` em `updater.requires_input(...)` — a Task vai para `TASK_STATE_INPUT_REQUIRED` com a linha exata `alternativas: <ids>`.

No lado do servidor, quem decide se há conflito e devolve a elicitation é o resolver `escolha_de_sala` ([`servidor-mcp/src/central_salas/adapters/mcp/mrtr.py:29`](servidor-mcp/src/central_salas/adapters/mcp/mrtr.py#L29)) — o agente nunca calcula alternativa nem conflito, só traduz o resultado em estado de Task.

**Volta — o `requestState` retorna ao servidor:**
1. Um novo `SendMessage` com `escolha=<id>` na mesma Task chega a `Ponte.continuar` ([`agente/src/agente_salas/application/ponte.py:74`](agente/src/agente_salas/application/ponte.py#L74)), que valida a escolha contra as alternativas guardadas e, se válida, remove a pendência (para não sobrar órfã se o retry falhar) antes de retomar.
2. `ClienteSalas.retomar` ([`agente/src/agente_salas/adapters/mcp_client/cliente.py:109`](agente/src/agente_salas/adapters/mcp_client/cliente.py#L109)) chama `reservar_sala` de novo pelo mesmo `_chamar_reservar_sala`, levando `inputResponses` com a mesma chave recebida e o `requestState` ecoado **sem modificação**. Como o cliente MCP do SDK gera um id de JSON-RPC novo por chamada (nunca reaberto por Task), esse retry chega ao servidor com um id diferente do request original.
3. O servidor valida a integridade do `requestState` (HMAC, ver "Decisões técnicas") e reconstrói o pedido original a partir dele — os argumentos reenviados pelo cliente nunca têm efeito.

O agente nunca abre, interpreta nem reconstrói o conteúdo do `requestState`: ele só guarda o que recebeu e devolve exatamente isso.

## Decisões técnicas

- **Selagem do `requestState`:** `RequestStateSecurity` do SDK `mcp` (HMAC sobre os argumentos + a identidade do request), chave única vinda de `REQUEST_STATE_SECRET`, nunca hardcoded — ver [`servidor-mcp/src/central_salas/adapters/mcp/server.py:68`](servidor-mcp/src/central_salas/adapters/mcp/server.py#L68) e a validação de tamanho mínimo (32 bytes) em [`servidor-mcp/src/central_salas/infra/config.py`](servidor-mcp/src/central_salas/infra/config.py). Uma adulteração de um único caractere é rejeitada com `-32602`.
- **TTL:** 10 minutos (`TTL_REQUEST_STATE_SEGUNDOS`, [`servidor-mcp/src/central_salas/constantes.py:16`](servidor-mcp/src/central_salas/constantes.py#L16)), dentro da faixa de 5–30 min exigida pelo enunciado. O `requestState` sobrevive a um restart do servidor porque carrega tudo que é necessário para reconstruir o pedido — nada fica em memória entre o `input_required` e o retry do lado do MCP.
- **Onde fica o estado das Tasks:** só em memória do agente, por processo. `InMemoryTaskStore` do `a2a-sdk` guarda o ciclo de vida da Task; `Pendencias` ([`agente/src/agente_salas/application/pendencias.py`](agente/src/agente_salas/application/pendencias.py)) guarda a `PendenciaMRTR` por `task_id` enquanto a Task está em `INPUT_REQUIRED`. Nenhum dos dois sobrevive a um restart do agente — só o `requestState`, que mora no servidor MCP e volta pelas mãos do cliente, precisa disso.
- **Um `ClienteSalas` por processo** (não por Task/requisição): abrir um cliente MCP novo a cada chamada reiniciaria a contagem de id do JSON-RPC em 1, fazendo o id do retry colidir com o da chamada original. O cliente vive no lifespan do app A2A; a descoberta de tools (`tools/list`) é lazy, mas sempre ocorre antes do primeiro `tools/call`.
- **Propagação do `traceparent`:** o agente lê o header `traceparent` do `SendMessage` inicial, guarda o trace-id junto com a `TaskPausada` e gera um span-id novo por chamada MCP (`TraceContext.com_novo_span`), nunca um trace-id novo. O servidor MCP registra `method`, `id` e `traceparent` de cada request no stderr.
- Limitações de SDK encontradas e os contornos adotados estão documentadas na [ADR-0002](docs/adr/0002-a2a-sdk.md), [ADR-0003](docs/adr/0003-cliente-mcp-do-agente.md) e [ADR-0006](docs/adr/0006-request-state.md), e resumidas em [`DESAFIOS.md`](DESAFIOS.md).

## Saída do validador

Execução contra os dois processos recém-iniciados (`scripts/validar.sh`, 2026-10-05):

```
trace-id desta execucao: 59c9c05cca8fe6216a2ac3bf6a473a6e
procure esse valor no stderr do servidor MCP para conferir a propagacao do traceparent.

PASS 01 tools/list traz as tres tools
PASS 02 toda tool tem inputSchema de objeto
PASS 03 listar_salas devolve structuredContent e o mesmo JSON em texto
PASS 04 _meta sem protocolVersion devolve -32602 e HTTP 400
PASS 05 _meta sem clientCapabilities devolve -32602 e HTTP 400
PASS 06 tool inexistente e recusada, por -32602 ou por isError
PASS 07 resources/read de politica://uso devolve a politica
PASS 08 resources/read de URI inexistente devolve -32602
PASS 09 sala inexistente devolve isError com a mensagem exata
PASS 10 fora da janela devolve isError com a mensagem exata
PASS 11 duracao acima de 2h devolve isError com a mensagem exata
PASS 12 intervalo invertido devolve isError com a mensagem exata
PASS 13 conflito devolve input_required com inputRequests e requestState
PASS 14 a elicitation e form mode e oferece as alternativas na ordem certa
PASS 15 conflito sem a capability elicitation devolve -32021 e HTTP 400
PASS 16 retry com inputResponses e requestState conclui a reserva
PASS 17 requestState adulterado e rejeitado com -32602
PASS 18 argumentos adulterados no retry nao tomam efeito
PASS 19 recusa conclui sem reservar e sem isError
PASS 20 conflito sem alternativa possivel devolve isError com a mensagem exata

PASS 21 agent card responde 200 no well-known com JSON
PASS 22 o card declara a interface JSON-RPC com url e versao 1.0
PASS 23 o card declara a skill reservar-sala
PASS 24 SendMessage com sala livre conclui a Task
PASS 25 o artifact chama reserva e traz a versao da politica
PASS 26 GetTask devolve id, contextId e estado corrente
PASS 27 SendMessage com sala ocupada pausa a Task
PASS 28 a Task pausada lista as alternativas na ordem certa
PASS 29 escolha fora do enum mantem a Task pausada
PASS 30 a continuacao conclui a Task na sala escolhida
PASS 31 SendMessage em Task terminal e recusado
PASS 32 a recusa termina a Task em CANCELED
PASS 33 duas Tasks pausadas ao mesmo tempo concluem cada uma com a sua reserva
PASS 34 nenhuma resposta A2A carrega o requestState
PASS 35 sala inexistente termina a Task em FAILED com a mensagem da tool
PASS 36 o agente e deterministico: o mesmo pedido produz a mesma pausa

resumo: 36 passaram, 0 falharam, de 36 verificacoes
```

Conferido também no stderr do servidor MCP: um `tools/list` antes do primeiro `tools/call` do agente, o trace-id do validador propagado em `traceparent` e, no par de `tools/call` de uma reserva que passou pela pausa, o id do retry diferente do id do request inicial. `grep -c Traceback logs/agente.log` dá `0`.

## Estrutura

```
.
├── docs/           # SDD: constituição, specs por fase, ADRs, progresso
├── dados/          # fixtures do domínio (não alterado)
├── validador/      # validador oficial (não alterado)
├── exemplos/wire/  # contrato de wire dos dois protocolos (não alterado)
├── servidor-mcp/   # domain / application / adapters/mcp / infra
└── agente/         # domain / application (ponte.py, pendencias.py) / adapters/a2a, adapters/mcp_client / infra
```

Camadas enxutas, sem ORM e sem import cruzado entre `servidor-mcp` e `agente` — eles só conversam por HTTP, como processos de verdade.
