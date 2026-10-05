# ADR-0005 — Arquitetura em camadas enxutas

- **Status:** aceito · **Data:** 2026-10-05

## Contexto
O usuário pediu arquitetura em camadas; o enunciado avisa que ORM, banco e camada de serviços são trabalho no lugar errado.

## Opções
- **Enxuta:** `domain` (puro) → `application` (casos de uso/ponte) → `adapters` (MCP, A2A) + `infra` (config, JSON, log). Prós: testável, clara, sem cerimônia. Contras: menos "livro-texto".
- **Hexagonal completa** com ports/DI. Prós: troca fácil. Contras: overengineering para 5 salas.

## Decisão
Enxuta. Regra: dependência só aponta para dentro; `domain` sem I/O nem SDK; abstração (Protocol) só onde há duas implementações reais (ex.: cliente MCP real × fake de teste).
