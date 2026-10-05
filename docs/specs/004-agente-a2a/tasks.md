# Tarefas — 004 agente A2A

- [x] T4.1 `domain/comando.py` parser fixo — TDD (válido, campos faltando, ordem trocada, escolha/recusar)
- [x] T4.2 `adapters/a2a/card.py` (card v1.0) + teste contra wire 07
- [x] T4.3 `adapters/a2a/executor.py` (AgentExecutor do a2a-sdk) + `app.py` (rotas `/a2a` e well-known), TaskStore em memória
- [x] T4.4 Caminho feliz: pedido → `ClienteSalas.reservar` → artifact `reserva` → COMPLETED
- [x] T4.5 Falha de tool → FAILED com mensagem exata; Task terminal recusa SendMessage
- [x] T4.6 Integração (ASGI + servidor MCP real) V21–V26, V31, V35 → PR
