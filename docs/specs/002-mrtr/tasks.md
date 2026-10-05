# Tarefas — 002 MRTR

- [x] T2.1 Ler docstrings do SDK (`input_required`, resolver, selagem) e registrar o desenho em ADR-0006
- [x] T2.2 `application/casos_de_uso`: separa consulta (`verificar_conflito_reserva`, só leitura) de gravação (`reservar_sala`, só grava) — TDD
- [x] T2.3 Adapter MCP (`mrtr.py`): resolver `escolha_de_sala` devolve `Elicit` com schema pydantic dinâmico (`create_model`+`Literal`); tool `reservar_sala` usa `Annotated[ElicitationResult[Any], Resolve(...)]` e grava
- [x] T2.4 Checagem de capability `elicitation.form` → `-32021` + HTTP 400 (automática do SDK quando o resolver emite `Elicit`; confirmado V15)
- [x] T2.5 Retry: estado inválido → `-32602` (V17), argumentos adulterados não têm efeito (V18, automático do SDK), `accept`/`decline`/`cancel` tratados na tool (V16, V19)
- [x] T2.6 Testes de integração V13–V20 + teste de restart (dois apps com o mesmo secret) + teste de expiração (relógio injetado via monkeypatch de `mcp.server.request_state.time`) — 8 testes novos em `test_app.py`
- [ ] T2.7 `rodar-validador` (V01–V20 verdes, confirmado) — AV11 (adulterado+expirado), AV12 (restart) e AV13 (sem capability) já cobertas pelos testes automatizados de T2.6, sem precisar de roteiro manual → falta abrir o PR
