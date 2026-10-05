# 004 — Agente como servidor A2A

**Branch:** `feature/agente-a2a` · **Modelo:** Sonnet · **Checks:** V21–V26, V31, V35, AV3

## Requisitos
- **A2A-01** `GET /.well-known/agent-card.json` → 200 com card v1.0 igual em forma a `exemplos/wire/07` (`supportedInterfaces[{url, protocolBinding: JSONRPC, protocolVersion: 1.0}]`, capabilities sem streaming/push). URL do endpoint vem de config. *(V21, V22)*
- **A2A-02** Skill `id: reservar-sala` com exemplo do formato fixo. *(V23)*
- **A2A-03** `/a2a` aceita `SendMessage` e `GetTask` (JSON-RPC 2.0). Sem streaming.
- **A2A-04** `SendMessage` sem `taskId` → Task nova (`id`, `contextId` próprios), transita `SUBMITTED → WORKING → terminal|INPUT_REQUIRED`. *(V24)*
- **A2A-05** Sucesso → `TASK_STATE_COMPLETED` + artifact `name="reserva"` com JSON `{reserva, sala, inicio, fim, responsavel, politica}`. *(V25)*
- **A2A-06** `GetTask` → `id`, `contextId`, estado corrente, artifacts, history. *(V26)*
- **A2A-07** `SendMessage` para Task terminal → erro JSON-RPC. *(V31)*
- **A2A-08** Erro de tool → `TASK_STATE_FAILED` com a mensagem exata da tool no `status.message` (e no history). Comando malformado → `FAILED` com mensagem de uso. *(V35)*
- **A2A-09** Determinismo: nenhuma aleatoriedade influencia o conteúdo das mensagens (ids de Task/mensagem podem ser aleatórios).

## Domínio do agente (só protocolo)
`domain/comando.py`: `parse("reservar sala=.. inicio=.. fim=.. responsavel=..") -> PedidoReserva`, `parse("escolha=..") -> Escolha(valor | RECUSAR)`. Sem validar regras de sala.
