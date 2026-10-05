# 003 — Agente como host MCP

**Branch:** `feature/agente-host-mcp` · **Modelo:** Sonnet · **Checks:** AV5, AV6, base para V24–V36

## Requisitos
- **HOST-01** Descoberta por `tools/list` antes do primeiro `tools/call` (no startup ou lazy na 1ª Task); nenhuma lista fixa usada para decidir chamada — o agente verifica que `reservar_sala` foi descoberta.
- **HOST-02** Lê `politica://uso` e extrai a versão da 1ª linha (`versao: X`) para o artifact.
- **HOST-03** Todo request: `_meta` com `protocolVersion=2026-07-28`, `clientInfo`, `clientCapabilities={"elicitation":{"form":{}}}`; headers `MCP-Protocol-Version`, `Mcp-Method`, e `Mcp-Name` em `tools/call`/`resources/read`.
- **HOST-04** `traceparent`: se a chamada A2A trouxe header, todos os requests MCP daquela Task levam `_meta.traceparent` com o **mesmo trace-id** e span-id novo. Trace-id guardado por Task para a continuação.
- **HOST-05** Resultado com `isError: true` vira falha propagada com a mensagem exata da tool (usada pela 004 para `TASK_STATE_FAILED`).
- **HOST-06** Cliente devolve `input_required` **cru** (chave, schema, `requestState`) — nunca responde a elicitation sozinho.
- **HOST-07** Retry com **id JSON-RPC novo**, `inputResponses` com a mesma chave, `requestState` byte a byte igual.
- **HOST-08** `requestState` tratado como `str` opaca: nenhum decode/parse no agente.

## Interface (porta) usada pela ponte
```python
class ClienteSalas:
    async def descobrir(self) -> None
    async def versao_politica(self, trace: TraceContext) -> str
    async def reservar(self, args: ArgsReserva, trace) -> Concluido | Falhou | PrecisaEntrada
    async def retomar(self, args, pendencia: PendenciaMRTR, resposta: RespostaElicitation, trace) -> Concluido | Falhou | Recusado | PrecisaEntrada
```
