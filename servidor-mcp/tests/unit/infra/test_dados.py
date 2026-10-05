import json
from pathlib import Path

from central_salas.infra.dados import carregar_politica, carregar_reservas, carregar_salas


def test_carregar_salas_le_json(tmp_path: Path) -> None:
    caminho = tmp_path / "salas.json"
    caminho.write_text(
        json.dumps([{"id": "sala-aquario", "nome": "Aquario", "capacidade": 4, "recursos": ["tv"]}])
    )
    salas = carregar_salas(caminho)
    assert len(salas) == 1
    assert salas[0].id == "sala-aquario"
    assert salas[0].recursos == ["tv"]


def test_carregar_reservas_le_json(tmp_path: Path) -> None:
    caminho = tmp_path / "reservas.json"
    caminho.write_text(
        json.dumps(
            [
                {
                    "id": "res-0001",
                    "sala": "sala-garagem",
                    "inicio": "2026-11-03T14:00:00-03:00",
                    "fim": "2026-11-03T15:00:00-03:00",
                    "responsavel": "Marty",
                }
            ]
        )
    )
    reservas = carregar_reservas(caminho)
    assert len(reservas) == 1
    assert reservas[0].id == "res-0001"
    assert reservas[0].responsavel == "Marty"


def test_carregar_politica_le_versao_da_primeira_linha(tmp_path: Path) -> None:
    caminho = tmp_path / "politica.md"
    caminho.write_text("versao: 2026-11-01\n\n- Reservas somente entre 08:00 e 20:00.\n")
    politica = carregar_politica(caminho)
    assert politica.versao == "2026-11-01"
    assert "08:00 e 20:00" in politica.texto
