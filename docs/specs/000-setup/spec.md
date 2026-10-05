# 000 — Setup do projeto

**Branch:** `feature/setup-projeto` · **Modelo:** Opus (spike) · **Checks:** nenhum diretamente

## Objetivo
Base executável e reprodutível para os dois processos, skills do projeto e a decisão pendente do cliente MCP (ADR-0003).

## Requisitos
- **SET-01** `uv` workspace na raiz com membros `servidor-mcp` e `agente`; Python `>=3.10,<3.13` declarado, 3.12 usado.
- **SET-02** Cada processo com seu `pyproject.toml`, deps com `==` e `uv.lock` commitado. Nenhum SDK de LLM.
- **SET-03** Ferramentas de qualidade (`ruff`, `mypy`, `pytest`, `pytest-asyncio`) como dev-deps, config única na raiz.
- **SET-04** Pacotes vazios em camadas (`domain/application/adapters/infra`) + `__main__.py` que sobe um app que responde.
- **SET-05** Config por env com defaults: `MCP_PORT=7301`, `AGENTE_PORT=7300`, `MCP_URL=http://127.0.0.1:7301/mcp`, `REQUEST_STATE_SECRET` (obrigatória no servidor; falha ao subir se ausente ou < 32 bytes).
- **SET-06** `.env.example` sem valores reais; `.env` já está no `.gitignore`.
- **SET-07** Skills do projeto criadas em `.claude/skills/`: `rodar-validador`, `git-flow`, `sdd-feature`, `conferir-wire`.
- **SET-08** Spike documentado em ADR-0003: o `ClientSession` do `mcp==2.3.0` (a) devolve `input_required` cru sem callback de elicitation? (b) permite `_meta` com `traceparent` por request? (c) envia `Mcp-Method`/`Mcp-Name`/`MCP-Protocol-Version`? (d) usa id novo no retry? Também localizar no SDK servidor: API de MRTR (`input_required`), utilitário de selagem de `requestState`, modo stateless.

## Critérios de aceite
- `uv sync` a partir de clone limpo funciona; `uv run ruff check . && uv run mypy && uv run pytest` verdes.
- `uv run --package servidor-mcp python -m central_salas` e `uv run --package agente python -m agente_salas` sobem nas portas padrão.
- ADR-0003 com decisão e evidência (trechos do SDK).
