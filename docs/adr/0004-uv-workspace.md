# ADR-0004 — `uv` workspace, um `pyproject.toml` por processo

- **Status:** aceito · **Data:** 2026-10-05

## Opções
- **uv + uv.lock** — Prós: lock com hashes, `uv sync`/`uv run`, rápido. Contras: exige instalar uv (1 linha no README).
- **pip + venv** — Prós: nada extra. Contras: sem lock de transitivas.
- **Um pyproject por processo** vs **um na raiz** — o primeiro reforça "dois processos separados" e impede import acidental do servidor pelo agente.

## Decisão
uv workspace na raiz (`members = ["servidor-mcp", "agente"]`), um `uv.lock`, config de ruff/mypy/pytest compartilhada na raiz.
