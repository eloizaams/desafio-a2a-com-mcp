# Tarefas — 001 servidor MCP

- [x] T1.1 `domain`: Sala, Reserva, Intervalo (parse ISO-8601 com offset), sobreposição semiaberta — TDD
- [x] T1.2 `domain/politica`: janela 08–20 em -03:00, duração ≤ 2h, intervalo invertido; ordem das validações — TDD com os 4 casos do validador
- [x] T1.3 `domain/alternativas`: regra (≠ pedida, livre, cap ≥, ordem (cap,id), máx 3) — TDD (caso garagem 14–15 → fusca, mirante)
- [x] T1.4 `infra`: carga de `salas.json`, `reservas.json`, política (+ versão); repositório em memória com gerador `res-NNNN`
- [x] T1.5 `application`: casos de uso listar / consultar / reservar (caminho livre)
- [x] T1.6 `adapters/mcp`: registrar tools com schemas de entrada/saída (pydantic), resource, URI inexistente → -32602
- [x] T1.7 Middleware/hook: validação de `_meta` (-32602 + HTTP 400) e log stderr (method, id, traceparent)
- [x] T1.8 Testes de integração ASGI (httpx) espelhando V01–V12; conferir com `conferir-wire` 01, 02, 05
- [x] T1.9 `rodar-validador` (V01–V12 verdes) → PR
