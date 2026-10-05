# Constituição do projeto — A Ponte (A2A + MCP)

Princípios que **toda** spec, plano, tarefa e PR deste repositório obedecem.
Se uma tarefa conflita com algo aqui, a tarefa está errada.

## 1. Inegociáveis do enunciado

1. **Dois processos separados.** `servidor-mcp/` e `agente/` são projetos Python independentes. O agente fala com o servidor só por HTTP. Nenhum `import` cruzado.
2. **Proibido alterar** `dados/`, `validador/`, `exemplos/`.
3. **Sem LLM** no caminho de execução. Nenhum SDK de provedor de LLM em `pyproject.toml`. Mesmo pedido → mesmo resultado.
4. **Sem sessão de protocolo.** Versão e capabilities são lidas do `_meta` de *cada* request. Nunca inferir de request anterior.
5. **Domínio só no servidor.** Conflito, política e alternativas são decididos pelo servidor MCP. O agente traduz protocolo, não domínio.
6. **`requestState` é opaco para o agente:** guardar, ecoar, nunca abrir, interpretar nem reconstruir. Nunca aparece em resposta A2A.
7. **`requestState` é selado** (HMAC/AEAD via utilitário do SDK), expira entre 5 e 30 min, chave de `REQUEST_STATE_SECRET` (≥ 32 bytes). Nenhum segredo no código ou no README.
8. **MRTR não é callback.** O servidor termina a resposta com `input_required`; o cliente volta com request novo e **id novo**.
9. **Mensagens de erro exatas** como no enunciado (fonte única: `docs/specs/PLANO.md` §Contratos).
10. Limitação real de SDK → documentar no README com evidência, nunca reescrever o protocolo.

## 2. Engenharia

- **Stack:** Python 3.12, `uv` (workspace), versões travadas (`==` + `uv.lock`). Ver ADR-0001..0004.
- **Camadas enxutas** (ADR-0005): `domain` (puro, sem I/O) → `application` (casos de uso / ponte) → `adapters` (MCP, A2A, HTTP) + `infra` (config, carga de JSON, log). Dependência só aponta para dentro. Sem ORM, sem banco, sem interfaces abstratas sem segunda implementação.
- **Clean code:** funções pequenas, nomes do domínio em português (como os dados e o enunciado), sem números/strings mágicas (constantes nomeadas), sem comentário que repete o código, sem código morto.
- **DRY:** mensagens de erro, nomes de tools, URI do resource, códigos JSON-RPC e chaves de `_meta` vivem em **um** módulo de constantes por processo.
- **Tipagem:** type hints em tudo; `mypy --strict` nos pacotes `domain` e `application`.
- **Qualidade:** `ruff check` + `ruff format` + `mypy` + `pytest` verdes antes de todo PR.
- **TDD** (skill `tdd`) no `domain` e na `application`. Testes de integração contra os apps ASGI. O validador é o teste de aceitação final.
- **Logs:** sempre em `stderr`, uma linha por request MCP com `method`, `id`, `traceparent`.

## 3. Processo

- **SDD:** nada de código sem spec. Fluxo: `spec.md` → (plano em `PLANO.md`) → `tasks.md` → código → marcar tarefa → validar.
- **Git flow manual** (ADR-0007): `main` (entrega) ← `release/x.y.z` ← `develop` ← `feature/*`. Nunca commitar direto em `main` ou `develop`; tudo entra por PR (skill `abrir-pr`).
- **Conventional Commits**, mensagens geradas pela skill `caveman-commit`. Escopos: `mcp`, `agente`, `ponte`, `docs`, `build`, `test`, `ci`.
- **Rastreabilidade:** todo requisito tem id (`MCP-xx`, `MRTR-xx`, `HOST-xx`, `A2A-xx`, `PONTE-xx`, `ENT-xx`) e aponta para o check do validador (`V01..V36`) ou passo do Fluxo do avaliador (`AV1..AV13`).
- **Contexto entre sessões:** `docs/PROGRESSO.md` é atualizado ao fim de cada tarefa. Fricções recorrentes vão para `DESAFIOS.md`.
