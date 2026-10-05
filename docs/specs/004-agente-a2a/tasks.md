# Tarefas — 004 agente A2A

- [ ] T4.1 `domain/comando.py` parser fixo — TDD (válido, campos faltando, ordem trocada, escolha/recusar)
- [ ] T4.2 `adapters/a2a/card.py` (card v1.0) + teste contra wire 07
- [ ] T4.3 `adapters/a2a/executor.py` (AgentExecutor do a2a-sdk) + `app.py` (rotas `/a2a` e well-known), TaskStore em memória
- [ ] T4.4 Caminho feliz: pedido → `ClienteSalas.reservar` → artifact `reserva` → COMPLETED
- [ ] T4.5 Falha de tool → FAILED com mensagem exata; Task terminal recusa SendMessage
- [ ] T4.6 Integração (ASGI + servidor MCP real) V21–V26, V31, V35 → PR
