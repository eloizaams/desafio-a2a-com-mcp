# ADR-0006 — Proteção e conteúdo do `requestState`

- **Status:** aceito (TTL 10 min confirmado; detalhes da API após T0.5/T2.1) · **Data:** 2026-10-05

## Decisão
- Selagem com o utilitário do SDK (`v1.` no wire de referência) — integridade obrigatória; cifra se o utilitário oferecer.
- Chave: `REQUEST_STATE_SECRET` (hex de 32 bytes, `secrets.token_hex(32)`); servidor não sobe sem ela.
- TTL: **10 minutos** (dentro de 5–30; tempo razoável para humano responder sem janela longa de replay).
- Conteúdo selado: `sala, inicio, fim, responsavel, alternativas, exp`. No retry o servidor usa só os valores selados (V18).
- Falha de verificação/expiração → `-32602` com a mensagem do SDK.
- Nada em memória entre `input_required` e retry ⇒ sobrevive a restart.

## Pendências
Confirmar API exata do SDK e o comportamento quando a sala escolhida foi ocupada entre pausa e retry.
