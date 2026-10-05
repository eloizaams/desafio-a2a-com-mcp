# Issue Tracker & Specs Mapping

This document guides the `code-review` skill to locate specs and standards for this project.

## Standards Sources

Code conventions and architectural decisions are documented in:

- **`docs/specs/constitution.md`** — core design principles, conventions, and language rules (Python, naming, error handling, etc.)
- **`docs/adr/`** — architecture decision records (ADR-0001 through ADR-0009+) capturing design trade-offs and rationales

The Standards axis in code review will inspect both files against the submitted diff.

## Specs Mapping

Project specifications are organized by phase under `docs/specs/`:

| Phase | Spec Path | Focus |
|-------|-----------|-------|
| **000-setup** | `docs/specs/000-setup/spec.md` | Initial project setup, dependencies, CI, structure |
| **001-servidor-mcp** | `docs/specs/001-servidor-mcp/spec.md` | MCP server implementation |
| **002-mrtr** | `docs/specs/002-mrtr/spec.md` | MRTR (Message Request/Response Tracing) |
| **003-agente-host-mcp** | `docs/specs/003-agente-host-mcp/spec.md` | Host-side MCP agent wrapper |
| **004-agente-a2a** | `docs/specs/004-agente-a2a/spec.md` | Agent-to-agent communication layer |
| **005-ponte** | `docs/specs/005-ponte/spec.md` | Bridge/integration layer |
| **006-entrega** | `docs/specs/006-entrega/spec.md` | Final delivery and validation |

### Locating Specs by Branch Name

When reviewing a branch like `feature/001-servidor-mcp` or `feature/002-mrtr`, the spec is at:
- `docs/specs/NNN-<slug>/spec.md` where `NNN` is the phase number extracted from the branch name.

Example: `feature/003-agente-host-mcp` → check `docs/specs/003-agente-host-mcp/spec.md`.

### Full Project Context

- **`docs/specs/ENUNCIADO.md`** — full project challenge statement (in Portuguese)
- **`docs/specs/PLANO.md`** — project plan and timeline
- **`docs/specs/constitution.md`** — design constitution (also used as Standards source)

## Workflow for Code Review Skill

The `code-review` skill will:

1. **Extract phase number** from the current branch name (e.g., `001`, `002`, etc.)
2. **Locate spec** at `docs/specs/NNN-*/spec.md` matching that phase
3. **Load standards** from `constitution.md` and `docs/adr/`
4. **Run parallel reviews** checking Standards (constitution + ADRs) and Spec (phase requirements)

If the phase cannot be determined from the branch, the skill will ask you to provide the spec path directly.
