---
name: git-flow
description: Git flow manual deste projeto (a CLI git-flow não está instalada) — iniciar feature a partir de develop, finalizar via PR, abrir release, merge em main com tag e back-merge. Use ao começar ou terminar uma fase, criar branch, "iniciar feature", "fechar a fase", "abrir release" ou "fazer o merge na main".
---

# Git flow manual (ADR-0007)

`main` (entrega) ← `release/x.y.z` ← `develop` ← `feature/*`. **Nunca** commitar direto em `main` ou `develop`; tudo entra por PR.

## Iniciar feature
Antes de criar a branch, confira `gh pr list` / `git log --oneline develop..origin/develop`: se o PR da fase anterior ainda estiver aberto (não mergeado), `develop` não tem o trabalho mais recente. Pergunte ao usuário se deve mergear aquele PR primeiro ou se a nova branch nasce de outro ponto — não assuma.
```bash
git checkout develop && git pull --ff-only origin develop
git checkout -b feature/<nome-da-fase>     # nome em docs/specs/PLANO.md §4
```

## Durante
- Commits pequenos, mensagem pela skill `caveman-commit` (Conventional Commits; escopos `mcp`, `agente`, `ponte`, `docs`, `build`, `test`, `ci`).
- Antes de commitar: `uv run ruff format . && uv run ruff check . && uv run mypy && uv run pytest -q`.

## Finalizar feature
1. Checks acima verdes + skill `rodar-validador` (checks esperados da fase).
2. Atualizar `docs/PROGRESSO.md` e marcar `tasks.md`.
3. Rodar `/code-review` sobre o diff da branch (antes de publicar — nunca pular) e aplicar os achados relevantes.
4. `git push -u origin feature/<nome>` e abrir PR **para `develop`** com a skill `abrir-pr`.
5. Após merge: `git checkout develop && git pull --ff-only && git branch -d feature/<nome>`.

## Release (fase 6)
```bash
git checkout develop && git pull --ff-only
git checkout -b release/1.0.0
# só ajustes de entrega (README, versão); PR release/1.0.0 → main via abrir-pr
```
Após merge na `main`:
```bash
git checkout main && git pull --ff-only
git tag -a v1.0.0 -m "Entrega A Ponte 1.0.0" && git push origin v1.0.0
git checkout develop && git merge --no-ff main && git push   # back-merge: só via PR se develop for protegida
```
Pergunte ao usuário antes de criar tag ou fazer push em `main`.
