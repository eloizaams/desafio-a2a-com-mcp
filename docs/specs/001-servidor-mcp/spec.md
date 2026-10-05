# 001 — Servidor MCP: tools, resource, erros, log

**Branch:** `feature/mcp-tools-basicas` · **Modelo:** Sonnet · **Checks:** V01–V12, AV2, AV5

## Requisitos
- **MCP-01** Request sem `io.modelcontextprotocol/protocolVersion` ou sem `io.modelcontextprotocol/clientCapabilities` no `_meta` → JSON-RPC `-32602` e HTTP `400`. Nunca inferir de request anterior. *(V04, V05)*
- **MCP-02** Streamable HTTP stateless em `:7301/mcp`, capabilities `tools` e `resources`. *(V01)*
- **MCP-03** Três tools com `inputSchema` objeto JSON Schema: `listar_salas` (sem params), `consultar_disponibilidade(sala, inicio, fim)`, `reservar_sala(sala, inicio, fim, responsavel)`. *(V01, V02)*
- **MCP-04** `listar_salas` com `outputSchema`; `structuredContent` == `json.loads(content[0].text)`. Todas as tools devolvem `structuredContent` + bloco de texto. *(V03)*
- **MCP-05** Validações de sala e política compartilhadas entre consultar e reservar, ordem: sala → intervalo invertido → janela → duração, com `isError: true` e mensagens exatas (PLANO §3). *(V09–V12)*
- **MCP-06** `consultar_disponibilidade` devolve `livre` (bool) e `conflitos` (lista de reservas). `reservar_sala` em intervalo livre cria reserva `res-NNNN` sequencial (seed: `dados/reservas.json`) com `structuredContent` = `{reserva, reservado, sala, inicio, fim, responsavel, politica, motivo}`. Reservas visíveis às consultas seguintes do mesmo processo.
- **MCP-07** Tool inexistente recusada (`-32602` ou `isError`). *(V06)*
- **MCP-08** Resource `politica://uso`, `mimeType text/markdown`, conteúdo de `dados/politica-de-uso.md`; URI inexistente → `-32602` (nunca `contents` vazio). *(V07, V08)*
- **MCP-09** Cada request logado em stderr: `method`, `id`, `traceparent` (ou `-`). *(AV5, AV6)*
- **MCP-10** `politica` no resultado = versão lida da 1ª linha da política (`versao: 2026-11-01`), não hardcoded.

## Domínio (puro, testado com TDD)
`Intervalo(inicio, fim)` com `sobrepoe()`; `validar_pedido(salas, sala_id, intervalo) -> ErroDominio | None`; `conflitos(reservas, sala, intervalo)`; `alternativas(salas, reservas, sala_pedida, intervalo)` (usado na 002).

## Fora
MRTR (conflito em `reservar_sala` nesta fase pode devolver erro provisório; vira `input_required` na 002).
