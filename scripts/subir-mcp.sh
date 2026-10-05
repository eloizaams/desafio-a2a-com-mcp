#!/usr/bin/env bash
# Sobe o servidor MCP (Central de Salas). Lê .env da raiz se existir.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -f .env ]]; then set -a; source .env; set +a; fi
exec uv run --package servidor-mcp python -m central_salas
