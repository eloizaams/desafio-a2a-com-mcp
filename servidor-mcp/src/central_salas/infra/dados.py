"""Carga dos arquivos em ``dados/`` (salas, reservas, política)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from central_salas.domain.modelos import Reserva, Sala


@dataclass(frozen=True)
class Politica:
    versao: str
    texto: str


def carregar_salas(caminho: Path) -> list[Sala]:
    bruto = json.loads(caminho.read_text())
    return [
        Sala(
            id=item["id"],
            nome=item["nome"],
            capacidade=item["capacidade"],
            recursos=item["recursos"],
        )
        for item in bruto
    ]


def carregar_reservas(caminho: Path) -> list[Reserva]:
    bruto = json.loads(caminho.read_text())
    return [
        Reserva(
            id=item["id"],
            sala=item["sala"],
            inicio=item["inicio"],
            fim=item["fim"],
            responsavel=item["responsavel"],
        )
        for item in bruto
    ]


def carregar_politica(caminho: Path) -> Politica:
    texto = caminho.read_text()
    primeira_linha = texto.splitlines()[0]
    _, _, versao = primeira_linha.partition(":")
    return Politica(versao=versao.strip(), texto=texto)
