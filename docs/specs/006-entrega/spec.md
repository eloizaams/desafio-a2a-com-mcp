# 006 — Entrega

**Branch:** `release/1.0.0` → `main` (tag `v1.0.0`) · **Modelo:** Sonnet; checklist Haiku · **Checks:** V01–V36, AV1–AV13

## Requisitos
- **ENT-01** README substituído com: Como rodar (de clone limpo: instalar uv, `uv sync`, gerar/exportar secret, subir os dois, rodar validador); Onde a ponte acontece (arquivo:linha); Decisões técnicas (selagem, TTL 10 min, onde fica o estado das Tasks); Saída completa do validador.
- **ENT-02** Validador 36/36, exit 0, processos recém-iniciados.
- **ENT-03** Roteiro manual AV1–AV13 executado e anotado em `docs/PROGRESSO.md`.
- **ENT-04** `git diff main..release -- dados validador exemplos` vazio.
- **ENT-05** Sem segredo no histórico (`security-review`); sem SDK de LLM nas deps.
- **ENT-06** Teste "do zero": clone do fork em pasta limpa seguindo só o README.
