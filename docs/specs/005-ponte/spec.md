# 005 — A ponte (MRTR ↔ Task)

**Branch:** `feature/ponte` · **Modelo:** Opus · **Checks:** V27–V30, V32–V34, V36, AV7–AV9

## Requisitos
- **PONTE-01** `PrecisaEntrada` → Task `TASK_STATE_INPUT_REQUIRED`, `status.message` texto **exato** `alternativas: <ids ", " na ordem do enum>`. *(V27, V28)*
- **PONTE-02** `PendenciaMRTR{chave, request_state, args, alternativas, trace_id}` guardada por `task_id` só no agente; nunca serializada em card/artifact/mensagem/log de resposta A2A. *(V34)*
- **PONTE-03** Continuação com `escolha=<id>` fora das alternativas → continua `INPUT_REQUIRED`, repete a mesma linha, **sem** chamar o MCP. *(V29)*
- **PONTE-04** Escolha válida → `retomar` (id novo, `inputResponses {chave: {action: accept, content: {sala}}}`, `requestState` ecoado) → COMPLETED com artifact da sala escolhida. Pendência removida. *(V30, AV8)*
- **PONTE-05** `escolha=recusar` → `action: decline` → `TASK_STATE_CANCELED`. *(V32, AV9)*
- **PONTE-06** Isolamento por Task: duas Tasks pausadas concluem cada uma com seu `requestState`. *(V33)*
- **PONTE-07** Mesmo pedido em conflito duas vezes → mesma linha de pausa byte a byte. *(V36)*
- **PONTE-08** Se o retry voltar `input_required` de novo (sala ocupada nesse meio-tempo), substitui a pendência e repete a pausa.
- **PONTE-09** Mensagem de continuação que não é `escolha=` em Task pausada → continua pausada, repete alternativas.
