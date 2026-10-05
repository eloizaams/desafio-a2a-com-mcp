# Progresso

> Atualizar ao fim de cada tarefa. Uma nova sessão começa lendo: este arquivo → `DESAFIOS.md` → `docs/specs/constitution.md` → `docs/specs/PLANO.md` → `tasks.md` da fase atual.

## Estado atual
- **Fase:** 1 — servidor MCP (`001-servidor-mcp`, concluída, aguardando PR) → próxima: Fase 2 `feature/mcp-mrtr`
- **Branch:** `feature/mcp-tools-basicas` (a partir de `develop`, PR #2 da fase 0 já mergeado)
- **Próxima tarefa:** T2.1 de `docs/specs/002-mrtr/tasks.md` · modelo sugerido: Opus (SDK MRTR) → Sonnet
- **PR aberto:** — (a abrir para esta fase)

## Validador
| Data | Resultado | Observação |
|------|-----------|------------|
| 2026-10-05 | 7/36 | Baseline da fase 0: só esqueleto (card mínimo, MCP sem tools). Pipeline `scripts/validar.sh` ok. |
| 2026-10-05 | 15/36 | Fim da fase 1: V01–V12 verdes (todo o escopo da fase). V13–V20 (MRTR) e maior parte de V21–V36 (A2A/ponte) falham como esperado — fora de escopo até as fases 2–5. |

## Log
- 2026-10-05 — Planejamento SDD, constituição, specs 000–006, ADRs 0001–0007. Decisões: Python 3.12, mcp 2.3.0, a2a-sdk 1.2.2, uv workspace, camadas enxutas, SDD leve, git flow manual.
- 2026-10-05 — Fase 0: uv workspace (raiz depende dos dois membros p/ `uv sync` instalar tudo), config ruff/mypy/pytest, camadas + `__main__`, config por env (TDD), apps mínimos com teste de integração, scripts, 4 skills em `.claude/skills/`. Spikes: ADR-0003 aceito (ClientSession do SDK, 4/4), ADR-0006 com API real (`Resolve`/`Elicit`, `RequestStateSecurity`, -32021 e -32602 automáticos, sobrevive a restart).
- 2026-10-05 — Fase 1 (`feature/mcp-tools-basicas`): domain puro com TDD (`Intervalo`/`Sala`/`Reserva`, `politica.validar_pedido`/`conflitos`, `alternativas`), infra (`dados.py`, `RepositorioEmMemoria` com `res-NNNN` sequencial), application (3 casos de uso), adapters/mcp (3 tools + resource `politica://uso`, esquemas pydantic batendo exatamente com `exemplos/wire/01,02,05`), middleware de log stderr. Validação de `_meta` (-32602/400) e tool/URI inexistente são automáticas do SDK (`classify_inbound_request`, `ResourceNotFoundError`) — nenhum código extra necessário; achado documentado na ADR-0006. Conflito em `reservar_sala` nesta fase é `isError` provisório (`ErroConflito`), substituído por MRTR na fase 2. 69 testes (unit+integração), ruff/mypy limpos, `rodar-validador` com V01–V12 verdes.
