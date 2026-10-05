"""Ponto de entrada: python -m central_salas."""

import os
import sys

import uvicorn

from central_salas.adapters.mcp.server import criar_app
from central_salas.constantes import HOST
from central_salas.infra.config import ErroConfig, carregar_config


def main() -> None:
    try:
        config = carregar_config(os.environ)
    except ErroConfig as erro:
        print(f"Configuração inválida: {erro}", file=sys.stderr)
        sys.exit(1)
    uvicorn.run(criar_app(config), host=HOST, port=config.porta)


if __name__ == "__main__":
    main()
