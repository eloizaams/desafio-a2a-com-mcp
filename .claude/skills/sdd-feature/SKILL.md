---
name: sdd-feature
description: Executa a próxima tarefa de uma fase seguindo o SDD do projeto (constituição → spec → tasks → TDD → marcar → PROGRESSO). Use ao "iniciar a fase N", "seguir para a próxima tarefa", "continuar a implementação" ou retomar o trabalho numa sessão nova.
---

# Fluxo SDD de uma feature

## 1. Carregar contexto (nesta ordem, só o necessário)
1. `docs/PROGRESSO.md` — fase atual, branch, próxima tarefa.
2. `DESAFIOS.md` — armadilhas conhecidas.
3. `docs/specs/constitution.md` — regras inegociáveis.
4. `docs/specs/PLANO.md` — §3 Contratos (strings exatas) e §4 da fase.
5. `docs/specs/0NN-*/spec.md` e `tasks.md` da fase; ADRs citados.

## 2. Branch
Se não estiver na branch da fase, usar a skill `git-flow` (iniciar feature).

## 3. Para cada tarefa `- [ ]` em `tasks.md`
1. Identifique os requisitos (`MCP-xx`, `MRTR-xx`…) e os checks `Vxx`/`AVx` que ela cobre.
2. `domain`/`application`: TDD (skill `tdd`) — teste vermelho → implementação mínima → verde → refatorar.
   `adapters`: teste de integração contra o app ASGI (`starlette.testclient.TestClient`, `base_url="http://127.0.0.1:<porta>"` — o MCP rejeita `Host: testserver` com 421).
3. Strings de contrato só via `constantes.py` (DRY). Nada de import cruzado entre `servidor-mcp` e `agente`.
4. `uv run ruff format . && uv run ruff check . && uv run mypy && uv run pytest -q`.
5. Marque `- [x]` em `tasks.md`; atualize "Estado atual" e "Log" de `docs/PROGRESSO.md`.
6. Commit pela skill `caveman-commit`.

## 4. Fim da fase
Skill `rodar-validador` → checks esperados verdes → skill `git-flow` (finalizar) → PR com `abrir-pr`.
Diga ao usuário se a próxima fase pede Opus, Sonnet ou Haiku (coluna "Modelo sugerido" do PLANO) e sugira compactar/nova sessão.
