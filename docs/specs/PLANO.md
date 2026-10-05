# Plano de implementação — A Ponte

> Documento-mestre do SDD. Leia junto com `constitution.md`.
> Specs por feature: `docs/specs/0NN-*/spec.md` + `tasks.md`. Decisões: `docs/adr/`.
> Progresso vivo: `docs/PROGRESSO.md`.

## 1. Decisões fechadas

| # | Decisão | Escolha | ADR |
|---|---------|---------|-----|
| 1 | Stack | Python 3.12 (wire de referência foi gerado com o SDK Python `mcp`) | 0001 |
| 2 | Servidor MCP | `mcp==2.3.0` (SDK oficial v2, spec `2026-07-28`), Streamable HTTP stateless | 0001 |
| 3 | Lado A2A | `a2a-sdk==1.2.2` (AgentExecutor + TaskStore em memória) | 0002 |
| 4 | Cliente MCP do agente | `mcp.Client(mode="2026-07-28")` + `client.session.call_tool(..., allow_input_required=True)` (spike T0.4: 4/4 critérios ok) | 0003 |
| 5 | Dependências | `uv` workspace + `uv.lock`, um `pyproject.toml` por processo | 0004 |
| 6 | Arquitetura | Camadas enxutas (domain / application / adapters / infra) | 0005 |
| 7 | `requestState` | Utilitário de selagem do SDK, chave `REQUEST_STATE_SECRET`, TTL **10 min** | 0006 |
| 8 | Processo | SDD leve + git flow manual com PRs + Conventional Commits | 0007 |
| 9 | Estado das Tasks | Em memória no agente (`InMemoryTaskStore` + mapa `task_id → PendenciaMRTR`) | 0002 |

## 2. Arquitetura

```
 cliente A2A (validador)                      agente  :7300                                servidor-mcp  :7301
 ───────────────────────     ┌──────────────────────────────────────────────┐     ┌───────────────────────────────────────┐
 GET /.well-known/agent-card │ adapters/a2a  ── card, AgentExecutor          │     │ adapters/mcp ── tools, resource,      │
 POST /a2a  SendMessage ────▶│      │  (traceparent do header → contexto)    │     │   middleware _meta (-32602/400),       │
            GetTask          │      ▼                                        │     │   log stderr (method,id,traceparent)   │
                             │ application/ponte  ◀── A PONTE ──▶            │HTTP │      │                                 │
                             │   input_required → TASK_STATE_INPUT_REQUIRED  │────▶│ application/casos de uso               │
                             │   guarda PendenciaMRTR(task_id)               │/mcp │   reservar (MRTR: input_required,      │
                             │   escolha → retry tools/call (id novo)        │◀────│   requestState selado, -32021)        │
                             │      │                                        │     │      │                                 │
                             │ domain/comando  (parser fixo, sem regra sala) │     │ domain  (política, conflito,           │
                             │ adapters/mcp_client (tools/list, resource,    │     │   alternativas, erros exatos)          │
                             │   _meta + headers Mcp-*, traceparent)         │     │ infra   (dados/*.json, config, log)    │
                             │ infra (config, store de pendências)           │     └───────────────────────────────────────┘
                             └──────────────────────────────────────────────┘
```

### 2.1 Estrutura de pastas

```
.
├── pyproject.toml                 # uv workspace (members: servidor-mcp, agente) + config ruff/mypy/pytest compartilhada
├── uv.lock
├── scripts/                       # subir-mcp.sh, subir-agente.sh, validar.sh (apoio, permitido na raiz)
├── docs/{specs,adr}/  docs/PROGRESSO.md   DESAFIOS.md
├── servidor-mcp/
│   ├── pyproject.toml             # dep: mcp==2.3.0 (+ uvicorn)
│   ├── src/central_salas/
│   │   ├── domain/                # modelos (Sala, Reserva, Intervalo), politica.py, alternativas.py, erros.py
│   │   ├── application/           # listar_salas, consultar_disponibilidade, reservar_sala (resultado + necessidade de escolha)
│   │   ├── adapters/mcp/          # server.py (tools/resource), schemas de saída, middleware _meta + log, mrtr.py
│   │   ├── infra/                 # config (porta, secret, caminho de dados), carga JSON, repositório em memória
│   │   ├── constantes.py          # mensagens exatas, nomes de tool, URI, códigos JSON-RPC
│   │   └── __main__.py            # python -m central_salas
│   └── tests/{unit,integration}/
└── agente/
    ├── pyproject.toml             # deps: a2a-sdk[http-server]==1.2.2, mcp==2.3.0, uvicorn
    ├── src/agente_salas/
    │   ├── domain/                # comando.py (parse "reservar ..." / "escolha=..."), artefato.py
    │   ├── application/           # ponte.py (orquestra Task ↔ MRTR), pendencias.py (porta simples)
    │   ├── adapters/a2a/          # card.py, executor.py, app.py
    │   ├── adapters/mcp_client/   # cliente.py (descoberta, resource, tools/call, retry), trace.py
    │   ├── infra/                 # config, store em memória
    │   ├── constantes.py
    │   └── __main__.py            # python -m agente_salas
    └── tests/{unit,integration}/
```

### 2.2 Onde a ponte acontece (para o README final)

- **Ida:** `agente/.../application/ponte.py` → ao receber `resultType == "input_required"` do cliente MCP: extrai a única chave de `inputRequests`, lê o `enum` (ou `const`) da elicitation, salva `PendenciaMRTR(chave, requestState, argumentos, alternativas, traceparent)` no store indexado por `task_id`, e chama `updater.requires_input(...)` com a mensagem `alternativas: a, b`.
- **Volta:** `SendMessage` com `taskId` → executor detecta Task em `INPUT_REQUIRED` → `ponte.retomar()` → valida escolha contra `alternativas` → `tools/call` com **id novo**, `inputResponses={chave: {...}}` e o `requestState` ecoado sem modificação.

## 3. Contratos (fonte única de strings)

| Constante | Valor |
|-----------|-------|
| `ERRO_SALA_INEXISTENTE` | `Sala inexistente: {id}` |
| `ERRO_JANELA` | `Fora da janela de uso: a politica permite reservas entre 08:00 e 20:00` |
| `ERRO_DURACAO` | `Duracao acima do limite: a politica permite no maximo 2 horas` |
| `ERRO_INTERVALO` | `Intervalo invalido: fim deve ser posterior a inicio` |
| `ERRO_SEM_ALTERNATIVAS` | `Sem alternativas disponiveis no intervalo` |
| `MSG_ELICITATION` | `A sala pedida esta ocupada nesse intervalo. Escolha uma alternativa.` |
| `MOTIVO_RECUSA` | `recusado` |
| Linha de pausa (agente) | `alternativas: {ids separados por ", "}` |
| Artifact | `name="reserva"`, texto JSON com `reserva, sala, inicio, fim, responsavel, politica` |

Ordem de validação no servidor: **sala → intervalo invertido → janela → duração → conflito**.
Intervalos semiabertos `[inicio, fim)`. Janela avaliada em `-03:00`: `inicio >= 08:00` e `fim <= 20:00`.
Alternativas: salas ≠ pedida, livres no intervalo, `capacidade >= pedida`, ordem `(capacidade, id)`, máx. 3.

## 4. Fases (cada fase = 1 feature branch = 1 PR em `develop`)

| Fase | Branch | Spec | Checks cobertos | Modelo sugerido |
|------|--------|------|-----------------|-----------------|
| 0 | `feature/setup-projeto` | `000-setup` | — (base, skills, spike) | **Opus** (spike de SDK é exploratório) |
| 1 | `feature/mcp-tools-basicas` | `001-servidor-mcp` | V01–V12 | Sonnet |
| 2 | `feature/mcp-mrtr` | `002-mrtr` | V13–V20, AV11–AV13 | Opus (SDK MRTR) → Sonnet |
| 3 | `feature/agente-host-mcp` | `003-agente-host-mcp` | AV5 (tools/list antes), traceparent | Sonnet |
| 4 | `feature/agente-a2a` | `004-agente-a2a` | V21–V26, V31, V35 | Sonnet |
| 5 | `feature/ponte` | `005-ponte` | V27–V30, V32–V34, V36 | Opus (é o núcleo avaliado) |
| 6 | `release/1.0.0` | `006-entrega` | V01–V36 limpo, AV1–AV13, README | Sonnet; checklist final Haiku |

Ao fim de cada fase: `ruff` + `mypy` + `pytest` + skill `rodar-validador` (checks esperados verdes) + PR.

## 5. Rastreabilidade validador → requisito

| Check | Requisito | Check | Requisito |
|-------|-----------|-------|-----------|
| V01–V02 | MCP-02, MCP-03 | V21–V23 | A2A-01, A2A-02 |
| V03 | MCP-04 | V24–V25 | A2A-04, A2A-05, HOST-02 |
| V04–V05 | MCP-01 | V26 | A2A-06 |
| V06 | MCP-07 | V27–V28 | PONTE-01 |
| V07–V08 | MCP-08 | V29 | PONTE-03 |
| V09–V12 | MCP-05, MCP-06 | V30 | PONTE-04 |
| V13–V14 | MRTR-01, MRTR-02 | V31 | A2A-07 |
| V15 | MRTR-05 | V32 | PONTE-05 |
| V16 | MRTR-06 | V33 | PONTE-06 |
| V17 | MRTR-03 | V34 | PONTE-02 |
| V18 | MRTR-04 | V35 | HOST-05 |
| V19 | MRTR-07 | V36 | PONTE-07 |
| V20 | MRTR-08 | AV5, AV6 | MCP-09, HOST-01, HOST-04 |

## 6. Skills do projeto

Já existentes (globais) e como entram no fluxo:

| Skill | Uso |
|-------|-----|
| `tdd` | Ciclo red→green no `domain` e `application` |
| `caveman-commit` | Mensagem de todo commit (Conventional Commits) |
| `abrir-pr` | PR de `feature/*` → `develop` e `release/*` → `main` |
| `code-review` | Revisão de cada feature branch contra constituição + spec |
| `design-docs` | ADRs em MADR |
| `simplify` | Passada de limpeza antes do PR |
| `security-review` | Antes do release (foco: `requestState`, segredo, vazamento) |
| `handoff` | Ao trocar de sessão no meio de uma fase |

A criar em `.claude/skills/` (Fase 0):

| Skill nova | O que faz | Por quê |
|------------|-----------|---------|
| `rodar-validador` | Mata processos nas portas 7300/7301, gera `REQUEST_STATE_SECRET` temporário, sobe os dois com stderr em `logs/`, roda `validar.py`, mostra resumo + falhas, procura o trace-id no log do MCP e confere `tools/list` antes do 1º `tools/call` e ids diferentes no par do retry | O validador **exige processos recém-iniciados**; fazer isso à mão a cada iteração é a maior fonte de falso negativo |
| `git-flow` | Comandos padronizados: iniciar feature a partir de `develop`, finalizar via PR, abrir `release/x.y.z`, merge em `main` + tag, back-merge em `develop` | git-flow CLI não está instalado; evita commit acidental em `main` |
| `sdd-feature` | Fluxo de uma feature: ler constituição + spec, pegar próxima tarefa de `tasks.md`, TDD, marcar checkbox, atualizar `docs/PROGRESSO.md` | Mantém o SDD disciplinado e o contexto portátil entre sessões |
| `conferir-wire` | Dado um passo de `exemplos/wire/NN-*.json`, executa o mesmo request contra o processo local e mostra um diff estrutural (ignorando ids, `requestState`, ids gerados) | Depuração rápida de forma de payload (card v1.0, `resultType`, erros) |

## 7. Riscos e mitigação

| Risco | Mitigação |
|-------|-----------|
| SDK cliente MCP fecha o MRTR sozinho (callback) e a Task nunca pausa | `allow_input_required=True` + callback-guarda que levanta erro (ADR-0003) |
| Reuso do id JSON-RPC no retry | Gerador de id monotônico/aleatório por request; teste unitário dedicado |
| `a2a-sdk` divergir do wire (forma do card, `result.task`) | Teste de integração comparando com `exemplos/wire/07..10`; skill `conferir-wire` |
| Rodar validador 2× sem reiniciar (falso negativo) | Skill `rodar-validador` sempre reinicia |
| `requestState` vazar em resposta A2A | Store só no agente; teste que varre todas as respostas A2A |
| Check V18 (args adulterados) | Servidor usa **valores selados** do `requestState` no retry |
| Segredo commitado | `.env` no `.gitignore`; README só mostra como gerar; `security-review` no release |
| `traceparent` não chega no MCP | Trace-id guardado por Task; span-id novo por request; teste de integração lendo o log |
