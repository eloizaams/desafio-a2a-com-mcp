# Tarefas — 000 setup

- [x] T0.1 Instalar `uv`; criar workspace raiz + `pyproject.toml` dos dois processos; `uv lock`
- [x] T0.2 Config compartilhada ruff/mypy/pytest na raiz; esqueleto de camadas + `__main__.py` + `constantes.py`
- [x] T0.3 `infra/config.py` nos dois processos (env + defaults + validação do secret) — TDD
- [x] T0.4 **Spike** cliente MCP do SDK vs `httpx` (script descartável em `scratch/`, fora do repo) → ADR-0003
- [x] T0.5 Spike servidor: localizar API de MRTR, selagem de `requestState`, stateless, middleware → notas em ADR-0006
- [x] T0.6 Criar skills `rodar-validador`, `git-flow`, `sdd-feature`, `conferir-wire` (skill `skill-creator`)
- [x] T0.7 `scripts/` de subida (`subir-mcp.sh`, `subir-agente.sh`, `validar.sh`, `conferir_wire.py`); `.env.example`; atualizar `docs/PROGRESSO.md` — PR → `develop` pendente de confirmação
