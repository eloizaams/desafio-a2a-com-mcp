# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

**A Ponte** is a two-process system implementing MCP server + A2A agent for room reservation. The challenge centers on stateless protocol bridging: when the MCP server needs user input (MRTR `input_required`), the agent pauses the A2A Task, guards the opaque `requestState`, and resumes with a new JSON-RPC id when the user responds.

**Stack:** Python 3.12, `uv` workspace, deterministic (no LLMs in execution path).

## Architecture at a Glance

```
validador (A2A client)
    ↓
agente :7300 (A2A server + MCP client)
    domain/ — command parsing, artifacts
    application/ — ponte.py orchestrates Task ↔ MRTR, stores PendenciaMRTR per task
    adapters/a2a/ — Agent Card, AgentExecutor, traceparent → context
    adapters/mcp_client/ — tools/list, resource/read, tools/call with allow_input_required=True
    ↓ HTTP /mcp
servidor-mcp :7301 (MCP server)
    domain/ — Sala, Reserva, policy, alternatives, error messages
    application/ — listar_salas, consultar_disponibilidade, reservar_sala (MRTR loop)
    adapters/mcp/ — Streamable HTTP server, tools, resource, _meta middleware, log stderr
    infra/ — config (REQUEST_STATE_SECRET validation), dados/*.json

Key: requestState is sealed (HMAC, TTL 10 min), opaque to agent. When server returns input_required:
1. Agent stores PendenciaMRTR(requestState, inputRequests key, alternatives, original args, traceparent)
2. Agent pauses Task with msg "alternativas: sala-a, sala-b"
3. Client responds with "escolha=sala-a"
4. Agent retries tools/call with **new JSON-RPC id**, inputResponses + requestState, same traceparent
```

## Commands

```bash
# Setup (one-time)
uv sync

# Lint & type check (must pass before PR)
uv run ruff check .          # style
uv run ruff format --check . # formatting (same tool config, root pyproject.toml)
uv run mypy                  # strict on domain/ and application/

# Test
uv run pytest                # unit + integration
uv run pytest -k "test_config" --package agente  # single test

# Run processes (each in separate terminal)
uv run --package servidor-mcp python -m central_salas    # :7301
uv run --package agente python -m agente_salas           # :7300

# Validate (with both servers running)
python3 validador/validar.py --agente http://localhost:7300 --mcp http://localhost:7301
```

## Project Structure

- **`docs/specs/`** — phase specs (000-setup, 001-servidor-mcp, etc.) with spec.md + tasks.md per phase
- **`docs/adr/`** — Architecture Decision Records (0001-stack, 0003-cliente-mcp, 0006-request-state, etc.)
- **`docs/specs/constitution.md`** — inviolable rules (no LLM, no cross-imports, exact error messages, stateless)
- **`docs/agents/issue-tracker.md`** — how code-review skill finds specs/standards
- **`docs/PROGRESSO.md`** — session progress (updated end of each task)
- **`DESAFIOS.md`** — recurring friction points
- **`pyproject.toml`** (root) — uv workspace + shared tool config (ruff, mypy, pytest)
- **`agente/src/agente_salas/constantes.py`** — all A2A strings, port, MCP_URL
- **`servidor-mcp/src/central_salas/constantes.py`** — all tool names, error messages, JSON-RPC codes

## Critical Details

### REQUEST_STATE_SECRET
- Loaded from environment only, never hardcoded
- Minimum 32 bytes (generate: `python3 -c "import secrets; print(secrets.token_hex(32))"`)
- TTL 10 min (per ADR-0006)
- Sealed with HMAC/AEAD via SDK utility; adultered state → `-32602`

### The Bridge (onde a ponte acontece)
- **Server side:** `input_required` response in `reservar_sala` when interval conflicts
- **Agent side:** when `resultType == "input_required"` arrives, agent:
  1. Extracts the single key from `inputRequests`
  2. Reads `enum` or `const` from elicitation schema (the alternatives)
  3. Saves `PendenciaMRTR(key, requestState, original_args, alternatives)` indexed by task_id
  4. Calls `updater.requires_input("alternativas: sala-a, sala-b")` to pause Task
- **Resume:** on `SendMessage` with same `taskId`, validate choice, then `tools/call` with **new JSON-RPC id**, same `traceparent`, `inputResponses={key: {...}}`, `requestState` echoed unchanged

### Tracing
- Agent reads `traceparent` from A2A client header (HTTP)
- Propagates same trace-id (not span-id) in `_meta` of all MCP requests for that Task
- Server logs `method`, `id`, `traceparent` to stderr

### Layering
- No cross-imports between `agente/` and `servidor-mcp/` (completely separate processes)
- Each has domain (pure, no I/O) → application (use cases) → adapters (HTTP/MCP) + infra (config, data load)
- No ORM, no DB, no abstract interfaces without two implementations; in-memory Task store and reservation repo

## Code Standards

- **Polish:** `ruff check`, `mypy --strict` (domain, application layers), `pytest` all green before PR
- **Commits:** `conventional-commits` with scopes (`mcp`, `agente`, `docs`, `build`, `ci`); use caveman-commit skill
- **Names:** Portuguese domain language (Sala, Reserva, politica, etc.), from enunciado.md
- **DRY:** error messages, tool names, JSON-RPC codes, port defaults → `constantes.py` per process
- **Secrets:** `REQUEST_STATE_SECRET` from env, never in code; `.env` in `.gitignore`
- **Git flow:** feature branches from develop → PR to develop → merge + back-merge to feature when appropriate

## When to Read Further

- **Full enunciado (requirements):** `docs/specs/ENUNCIADO.md` (Portuguese, 463 lines)
- **Acceptance checklist:** see ✅ boxes in section "Critérios de Aceite" in PLANO.md
- **Current phase spec:** e.g., `docs/specs/001-servidor-mcp/spec.md` for MCP server tasks
- **Code review standards:** see `docs/specs/constitution.md` and `docs/adr/` for decisions
- **Example wire protocol:** `exemplos/wire/` contains JSON request/response pairs for every major flow

## Session Workflow

1. Read `docs/PROGRESSO.md` to see where the last session stopped
2. Check `DESAFIOS.md` for known friction (e.g., SDK limitations, tricky test scenarios)
3. Pick the next phase spec from `docs/specs/NNN-*/spec.md` and its `tasks.md`
4. Run tests and validador frequently; stderr of servidor-mcp is your debugging window (tools/list, traceparent, retry id)
5. Update PROGRESSO.md and DESAFIOS.md at end of session
6. Code review via `/code-review` (skill auto-finds constitution.md + ADRs as standards, spec as requirements)
