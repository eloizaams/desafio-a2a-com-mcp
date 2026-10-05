# Tarefas — 003 agente host MCP

- [x] T3.1 `adapters/mcp_client/trace.py`: parse/geração de `traceparent` (mesmo trace-id, span novo) — TDD
- [x] T3.2 Cliente conforme ADR-0003 (SDK sem callback ou `httpx`): `_meta`, headers, ids únicos — TDD com transporte fake
- [x] T3.3 Tipos de resultado `Concluido | Falhou | PrecisaEntrada | Recusado`; parse do `input_required` (enum ou const)
- [x] T3.4 Descoberta + leitura da política (versão)
- [ ] T3.5 Script de fumaça `python -m agente_salas.smoke`: reserva livre, conflito, retry manual (passo 6 do enunciado)
- [ ] T3.6 Integração contra servidor real em subprocesso: log mostra tools/list antes de tools/call e traceparent → PR
