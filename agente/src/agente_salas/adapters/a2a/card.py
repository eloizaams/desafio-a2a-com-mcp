"""Agent Card v1.0 do agente (A2A-01, A2A-02)."""

from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentProvider, AgentSkill

from agente_salas.constantes import (
    CAMINHO_A2A,
    DESCRICAO_AGENTE,
    HOST,
    MODO_TEXTO,
    NOME_AGENTE,
    PROVEDOR_ORGANIZACAO,
    PROVEDOR_URL,
    SKILL_RESERVAR_DESCRICAO,
    SKILL_RESERVAR_EXEMPLO,
    SKILL_RESERVAR_ID,
    SKILL_RESERVAR_NOME,
    SKILL_RESERVAR_TAGS,
    VERSAO_AGENTE,
    VERSAO_PROTOCOLO_A2A,
)
from agente_salas.infra.config import ConfigAgente


def criar_agent_card(config: ConfigAgente) -> AgentCard:
    return AgentCard(
        name=NOME_AGENTE,
        description=DESCRICAO_AGENTE,
        provider=AgentProvider(organization=PROVEDOR_ORGANIZACAO, url=PROVEDOR_URL),
        version=VERSAO_AGENTE,
        supported_interfaces=[
            AgentInterface(
                url=f"http://{HOST}:{config.porta}{CAMINHO_A2A}",
                protocol_binding="JSONRPC",
                protocol_version=VERSAO_PROTOCOLO_A2A,
            )
        ],
        capabilities=AgentCapabilities(
            streaming=False, push_notifications=False, extended_agent_card=False
        ),
        default_input_modes=[MODO_TEXTO],
        default_output_modes=[MODO_TEXTO],
        skills=[
            AgentSkill(
                id=SKILL_RESERVAR_ID,
                name=SKILL_RESERVAR_NOME,
                description=SKILL_RESERVAR_DESCRICAO,
                tags=list(SKILL_RESERVAR_TAGS),
                input_modes=[MODO_TEXTO],
                output_modes=[MODO_TEXTO],
                examples=[SKILL_RESERVAR_EXEMPLO],
            )
        ],
    )
