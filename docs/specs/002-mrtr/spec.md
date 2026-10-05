# 002 — Ciclo MRTR em `reservar_sala`

**Branch:** `feature/mcp-mrtr` · **Modelo:** Opus no início (API do SDK), depois Sonnet · **Checks:** V13–V20, AV11–AV13

## Requisitos
- **MRTR-01** Conflito com alternativas → `resultType: "input_required"`, `inputRequests` com **uma** entrada `elicitation/create`, `mode: "form"`, mensagem `MSG_ELICITATION`, e `requestState`. Chave atribuída pelo SDK. *(V13)*
- **MRTR-02** `requestedSchema` plano: `{type: object, properties: {sala: {type: string, enum|const: [...]}}, required: [sala]}` na ordem da regra de alternativas. *(V14, AV7)*
- **MRTR-03** `requestState` selado (utilitário do SDK) com HMAC/AEAD, chave `REQUEST_STATE_SECRET`, TTL 10 min. Adulterado ou expirado → `-32602`. Nunca 500. *(V17, AV11)*
- **MRTR-04** No retry, argumentos reenviados não tomam efeito: usar os **valores selados** (sala, inicio, fim, responsavel). *(V18)*
- **MRTR-05** Cliente sem `elicitation.form` declarado em `clientCapabilities` → `-32021`, `data.requiredCapabilities = {"elicitation": {"form": {}}}`, HTTP `400`. *(V15, AV13)*
- **MRTR-06** Retry lê `inputResponses` e `requestState` de `params`, reconstrói o pedido só do estado selado, valida que a sala escolhida ∈ alternativas seladas, e reserva. `resultType: complete`. Funciona após restart do processo (nada em memória entre as duas chamadas). *(V16, AV12)*
- **MRTR-07** `action` `decline`/`cancel` → `complete`, `isError` falso, `structuredContent.reservado=false`, `motivo="recusado"`. *(V19)*
- **MRTR-08** Conflito sem alternativas → `isError: true`, `ERRO_SEM_ALTERNATIVAS`, sem elicitation. *(V20)*

## Notas
- No retry, revalidar disponibilidade da sala escolhida (pode ter sido ocupada entre a pausa e o retry): se ocupada, nova pausa com alternativas recalculadas é aceitável; documentar no ADR-0006.
- A verificação de capability só acontece quando a elicitation seria emitida (conflito), não em toda chamada.
