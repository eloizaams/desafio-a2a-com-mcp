# Tarefas — 005 ponte

- [ ] T5.1 `application/pendencias.py`: store por task_id (get/put/pop) — TDD
- [ ] T5.2 `application/ponte.py`: `iniciar(pedido)` e `retomar(task, escolha)` retornando decisões de estado (puro, cliente fake) — TDD cobrindo PONTE-01..09
- [ ] T5.3 Executor: rotear Task em INPUT_REQUIRED para `retomar`; `requires_input` / `complete` / `cancel` / `failed`
- [ ] T5.4 Teste de não-vazamento: varrer todas as respostas A2A de um fluxo completo procurando o `requestState`
- [ ] T5.5 Integração ponta a ponta com os dois processos (V27–V36) → `rodar-validador` 36/36 → PR
