# Tarefas — 002 MRTR

- [ ] T2.1 Ler docstrings do SDK (`input_required`, resolver, selagem) e registrar o desenho em ADR-0006
- [ ] T2.2 `application/reservar`: resultado tipado `Reservada | PrecisaEscolha(alternativas) | Recusada | ErroDominio` — TDD
- [ ] T2.3 Adapter MCP: `PrecisaEscolha` → `input_required` com elicitation form + `requestState` selado (args + alternativas + exp)
- [ ] T2.4 Checagem de capability `elicitation.form` → `-32021` + HTTP 400
- [ ] T2.5 Retry: verificar estado (falha → -32602), usar valores selados, aplicar `accept` / `decline` / `cancel`
- [ ] T2.6 Testes de integração V13–V20 + teste de restart (dois apps com o mesmo secret) + teste de expiração (relógio injetado)
- [ ] T2.7 `rodar-validador` (V01–V20 verdes); roteiro manual AV11–AV13 → PR
