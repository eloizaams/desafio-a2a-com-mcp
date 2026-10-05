# Progresso

> Atualizar ao fim de cada tarefa. Uma nova sessão começa lendo: este arquivo → `DESAFIOS.md` → `docs/specs/constitution.md` → `docs/specs/PLANO.md` → `tasks.md` da fase atual.

## Estado atual
- **Fase:** 0 — setup (concluída, aguardando PR) → próxima: Fase 1 `feature/mcp-tools-basicas`
- **Branch:** `feature/setup-projeto` (a partir de `develop`)
- **Próxima tarefa:** T1.1 de `docs/specs/001-servidor-mcp/tasks.md` · modelo sugerido: Sonnet
- **PR aberto:** — (#1 já mergeado)

## Validador
| Data | Resultado | Observação |
|------|-----------|------------|
| 2026-10-05 | 7/36 | Baseline da fase 0: só esqueleto (card mínimo, MCP sem tools). Pipeline `scripts/validar.sh` ok. |

## Log
- 2026-10-05 — Planejamento SDD, constituição, specs 000–006, ADRs 0001–0007. Decisões: Python 3.12, mcp 2.3.0, a2a-sdk 1.2.2, uv workspace, camadas enxutas, SDD leve, git flow manual.
- 2026-10-05 — Fase 0: uv workspace (raiz depende dos dois membros p/ `uv sync` instalar tudo), config ruff/mypy/pytest, camadas + `__main__`, config por env (TDD), apps mínimos com teste de integração, scripts, 4 skills em `.claude/skills/`. Spikes: ADR-0003 aceito (ClientSession do SDK, 4/4), ADR-0006 com API real (`Resolve`/`Elicit`, `RequestStateSecurity`, -32021 e -32602 automáticos, sobrevive a restart).
