---
name: rodar-validador
description: Roda o validador oficial do desafio (validador/validar.py, 36 checks) com servidor MCP e agente recém-iniciados, e confere o trace-id no stderr do MCP. Use SEMPRE que for rodar o validador, conferir checks V01–V36, "ver quantos passam", validar uma fase antes do PR ou depurar um FAIL — nunca rode validar.py à mão com processos já em uso.
---

# Rodar o validador

O validador exige processos **recém-iniciados**: reservas criadas numa execução mudam a próxima (falso negativo). Por isso tudo passa por `scripts/validar.sh`.

## Passos

1. Na raiz do repo: `scripts/validar.sh` (timeout ~120 s). Ele:
   - mata o que estiver em 7300/7301 (`fuser -k`);
   - gera `REQUEST_STATE_SECRET` temporário;
   - sobe os dois processos com stderr em `logs/mcp.log` e `logs/agente.log`;
   - roda `validador/validar.py`, salva em `logs/validador.log`;
   - imprime resumo PASS/FAIL e se o trace-id da execução aparece em `logs/mcp.log`;
   - derruba os processos ao sair.
2. Reporte ao usuário: resumo `N PASS / M FAIL`, lista dos FAIL com o motivo, e o resultado do trace-id.
3. Compare com os checks esperados da fase (tabela §4 e §5 de `docs/specs/PLANO.md`). FAIL fora do escopo da fase atual é esperado — diga isso explicitamente.
4. Registre a linha na tabela "Validador" de `docs/PROGRESSO.md` (data, resultado, observação).

## Sempre conferir também
- `grep -c Traceback logs/agente.log` deve dar `0`. Um FAIL com `estado=` vazio quase sempre é exceção do a2a-sdk no agente (ex.: `Context in event doesn't match TaskManager`, fase 005) — o validador só vê o erro JSON-RPC, a causa está nesse log.

## Conferências extras do Fluxo do avaliador (manuais, quando a fase pede)
- **tools/list antes do 1º tools/call** (AV5): em `logs/mcp.log`, a primeira linha com `method=tools/call` deve vir depois de uma `method=tools/list`.
- **ids diferentes no retry**: as duas linhas `tools/call` do mesmo trace devem ter `id` distintos.
- **requestState após restart** (AV11–AV13): não é coberto pelo script — reinicie só o MCP com o **mesmo** segredo e reenvie o retry.

## Depurar um FAIL
Use a skill `conferir-wire` com o exemplo de `exemplos/wire/` correspondente ao check.
