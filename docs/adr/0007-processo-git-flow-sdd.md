# ADR-0007 — SDD leve + git flow manual + Conventional Commits

- **Status:** aceito · **Data:** 2026-10-05

## Decisão
- SDD em `docs/specs/` (constituição, PLANO, spec+tasks por feature).
- Git flow sem a CLI: `main` ← `release/x.y.z` ← `develop` ← `feature/*`, tudo via PR (skill `abrir-pr`); tag `v1.0.0` na main; back-merge em develop.
- Conventional Commits via skill `caveman-commit`.

## Prós / contras
Sem ferramenta extra, PRs viram evidência; custo: comandos manuais (skill `git-flow` mitiga). spec-kit descartado por boilerplate.
