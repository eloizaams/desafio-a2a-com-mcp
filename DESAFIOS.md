# Desafios e fricções recorrentes

Ler no início de cada sessão. Formato: problema → como lidar.

- **Validador exige processos recém-iniciados.** Reservas criadas numa execução mudam a seguinte → sempre usar a skill `rodar-validador` (reinicia tudo).
- **git-flow CLI não instalado.** Git flow é manual (ADR-0007) → usar skill `git-flow`; nunca commitar em `main`/`develop`.
- **`uv` não vem instalado.** Instalar com `curl -LsSf https://astral.sh/uv/install.sh | sh` (documentar no README).
- **Agente de commit:** o CLAUDE.md global cita "caverman-commit"; o que existe é a skill `caveman-commit`.
- **Pasted text longo pode não chegar.** O enunciado completo está no `README.md` do starter (será substituído na entrega → cópia em `docs/specs/ENUNCIADO.md`).
