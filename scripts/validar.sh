#!/usr/bin/env bash
# Roda o validador com os dois processos recém-iniciados.
# Mata o que estiver nas portas, gera REQUEST_STATE_SECRET temporário, sobe os dois com
# stderr em logs/, roda validador/validar.py, confere o trace-id no log do MCP e derruba tudo.
set -uo pipefail
cd "$(dirname "$0")/.."

PORTA_AGENTE="${AGENTE_PORT:-7300}"
PORTA_MCP="${MCP_PORT:-7301}"
LOGS=logs
mkdir -p "$LOGS"

liberar_porta() { fuser -k "$1/tcp" >/dev/null 2>&1 || true; }

esperar_porta() {
  for _ in $(seq 1 50); do
    (exec 3<>"/dev/tcp/127.0.0.1/$1") 2>/dev/null && return 0
    sleep 0.2
  done
  echo "ERRO: nada respondeu na porta $1 (veja $LOGS/)" >&2
  return 1
}

derrubar() { kill "${PID_MCP:-}" "${PID_AGENTE:-}" 2>/dev/null; wait 2>/dev/null; }
trap derrubar EXIT

liberar_porta "$PORTA_AGENTE"
liberar_porta "$PORTA_MCP"

export REQUEST_STATE_SECRET
REQUEST_STATE_SECRET="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"

uv run --package servidor-mcp python -m central_salas 2>"$LOGS/mcp.log" >/dev/null &
PID_MCP=$!
uv run --package agente python -m agente_salas 2>"$LOGS/agente.log" >/dev/null &
PID_AGENTE=$!
esperar_porta "$PORTA_MCP" && esperar_porta "$PORTA_AGENTE" || exit 1

python3 validador/validar.py \
  --agente "http://127.0.0.1:$PORTA_AGENTE" \
  --mcp "http://127.0.0.1:$PORTA_MCP" | tee "$LOGS/validador.log"
CODIGO=${PIPESTATUS[0]}

echo
echo "== Resumo: $(grep -c '^PASS' "$LOGS/validador.log") PASS, $(grep -c '^FAIL' "$LOGS/validador.log") FAIL"
TRACE_ID="$(grep -oE '[0-9a-f]{32}' "$LOGS/validador.log" | head -1)"
if [[ -n "$TRACE_ID" ]] && grep -q "$TRACE_ID" "$LOGS/mcp.log"; then
  echo "== trace-id $TRACE_ID encontrado no stderr do MCP ($(grep -c "$TRACE_ID" "$LOGS/mcp.log") linhas)"
else
  echo "== trace-id ${TRACE_ID:-?} NÃO encontrado em $LOGS/mcp.log"
fi
exit "$CODIGO"
