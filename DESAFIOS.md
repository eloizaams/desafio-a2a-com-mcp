# Desafios e fricções recorrentes

Ler no início de cada sessão. Formato: problema → como lidar.

- **Validador exige processos recém-iniciados.** Reservas criadas numa execução mudam a seguinte → sempre usar a skill `rodar-validador` (reinicia tudo).
- **git-flow CLI não instalado.** Git flow é manual (ADR-0007) → usar skill `git-flow` (`.claude/skills/git-flow`); nunca commitar em `main`/`develop`.
- **`uv` no terminal do VS Code (snap) cai no diretório errado.** O snap redefine `XDG_DATA_HOME`, e o instalador põe o binário em `~/snap/code/<rev>/.local/bin` (some quando o VS Code atualiza). Instalar com `curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=$HOME/.local/bin UV_NO_MODIFY_PATH=1 sh`. Já instalado: uv 0.12.23 em `~/.local/bin`.
- **Agente de commit:** o CLAUDE.md global cita "caverman-commit"; o que existe é a skill `caveman-commit`.
- **Pasted text longo pode não chegar.** O enunciado completo está no `README.md` do starter (será substituído na entrega → cópia em `docs/specs/ENUNCIADO.md`).
- **MCP rejeita `Host: testserver` com 421** (proteção DNS rebinding do SDK). Em testes ASGI usar `TestClient(app, base_url="http://127.0.0.1:7301")`.
- **`pkill -f <padrão>` mata o próprio shell** quando o padrão aparece na linha de comando do Bash. Derrubar processos por porta (`fuser -k 7301/tcp`) ou por PID (`$!`).
- **Cliente MCP do SDK só anuncia `elicitation` se houver `elicitation_callback`.** Passar um callback-guarda que levanta erro e sempre chamar `client.session.call_tool(..., allow_input_required=True)` — nunca `Client.call_tool` (fecha o MRTR sozinho). Ver ADR-0003.
- **ruff N818 desligado:** exceções seguem o domínio em português (`ErroX`).
