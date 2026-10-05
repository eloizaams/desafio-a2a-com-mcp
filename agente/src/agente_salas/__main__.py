"""Ponto de entrada: python -m agente_salas."""

import os
import sys

import uvicorn

from agente_salas.adapters.a2a.app import criar_app
from agente_salas.constantes import HOST
from agente_salas.infra.config import ErroConfig, carregar_config


def main() -> None:
    try:
        config = carregar_config(os.environ)
    except ErroConfig as erro:
        sys.exit(f"Configuração inválida: {erro}")
    uvicorn.run(criar_app(config), host=HOST, port=config.porta)


if __name__ == "__main__":
    main()
