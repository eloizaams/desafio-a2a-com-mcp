#!/usr/bin/env bash
# Sobe o agente A2A (host MCP). Lê .env da raiz se existir.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -f .env ]]; then set -a; source .env; set +a; fi
exec uv run --package agente python -m agente_salas
