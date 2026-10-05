---
name: conferir-wire
description: Compara a resposta do processo local com um exemplo de referência em exemplos/wire/NN-*.json (diff estrutural ignorando ids, requestState e campos gerados). Use ao depurar um FAIL do validador, ao conferir forma de payload (Agent Card, resultType, inputRequests, erros JSON-RPC, Task A2A) ou quando o usuário pedir para "comparar com o wire".
---

# Conferir contra o wire de referência

## Mapa rápido
| NN | Passo | NN | Passo |
|----|-------|----|-------|
| 01 | tools/list | 07 | Agent Card |
| 02 | tools/call livre | 08 | A2A SendMessage |
| 03 | conflito → input_required | 09 | GetTask em INPUT_REQUIRED |
| 04 | retry com inputResponses | 10 | SendMessage de continuação |
| 05 | resources/read política | 11 | retry com recusa |
| 06 | erro -32021 sem elicitation | | |

## Passos
1. O processo alvo precisa estar no ar (`scripts/subir-mcp.sh` com `REQUEST_STATE_SECRET` exportada, ou `scripts/subir-agente.sh`). Para exemplos de conflito (03, 04, 11) suba do zero — reservas anteriores mudam o resultado.
2. `python3 scripts/conferir_wire.py NN`
   - Retry (04, 11): primeiro rode o 03, copie o `requestState` da resposta e passe `--request-state v1.…`.
   - Passos A2A 09/10 dependem de `taskId` real: prefira reproduzir pelo validador e usar este script só para a forma.
3. Leia o diff: `- faltando` (campo do wire ausente), `+ sobrando` (campo extra), `~ valor` (diferença). Ids, `requestState` e ids gerados são ignorados.
4. Corrija respeitando a constituição: divergência causada pelo SDK que não dá para resolver sem reescrever o protocolo → documentar no README com evidência.
