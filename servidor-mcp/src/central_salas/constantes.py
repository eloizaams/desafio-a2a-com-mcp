"""Fonte única de nomes, valores padrão e contratos do servidor MCP."""

from typing import Final

NOME_SERVIDOR: Final = "central-de-salas"
VERSAO_SERVIDOR: Final = "1.0.0"

HOST: Final = "127.0.0.1"
CAMINHO_MCP: Final = "/mcp"

ENV_PORTA: Final = "MCP_PORT"
ENV_SEGREDO: Final = "REQUEST_STATE_SECRET"
PORTA_PADRAO: Final = 7301
TAMANHO_MINIMO_SEGREDO_BYTES: Final = 32
COMANDO_GERAR_SEGREDO: Final = "python3 -c 'import secrets; print(secrets.token_hex(32))'"
TTL_REQUEST_STATE_SEGUNDOS: Final = 10 * 60

# Nomes de tool e URI de resource (PLANO.md §2.1)
TOOL_LISTAR_SALAS: Final = "listar_salas"
TOOL_CONSULTAR_DISPONIBILIDADE: Final = "consultar_disponibilidade"
TOOL_RESERVAR_SALA: Final = "reservar_sala"
URI_POLITICA: Final = "politica://uso"

# Caminhos dos dados (dados/ não pode ser alterado; raiz = cwd do processo)
CAMINHO_SALAS: Final = "dados/salas.json"
CAMINHO_RESERVAS: Final = "dados/reservas.json"
CAMINHO_POLITICA: Final = "dados/politica-de-uso.md"

PREFIXO_RESERVA: Final = "res-"
DIGITOS_ID_RESERVA: Final = 4

# Política de uso (domain/politica.py)
JANELA_HORA_INICIO: Final = 8
JANELA_HORA_FIM: Final = 20
DURACAO_MAXIMA_HORAS: Final = 2
FUSO_POLITICA_HORAS: Final = -3
MAXIMO_ALTERNATIVAS: Final = 3

# Mensagens de erro exatas (PLANO.md §3 Contratos — fonte única)
ERRO_SALA_INEXISTENTE: Final = "Sala inexistente: {sala_id}"
ERRO_JANELA: Final = "Fora da janela de uso: a politica permite reservas entre 08:00 e 20:00"
ERRO_DURACAO: Final = "Duracao acima do limite: a politica permite no maximo 2 horas"
ERRO_INTERVALO: Final = "Intervalo invalido: fim deve ser posterior a inicio"
ERRO_SEM_ALTERNATIVAS: Final = "Sem alternativas disponiveis no intervalo"
MSG_ELICITATION: Final = "A sala pedida esta ocupada nesse intervalo. Escolha uma alternativa."
MOTIVO_RECUSA: Final = "recusado"
