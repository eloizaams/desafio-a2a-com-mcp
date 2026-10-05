from agente_salas.application.pendencias import Pendencias, TaskPausada
from agente_salas.domain.pendencia import ArgsReserva, PendenciaMRTR
from agente_salas.domain.trace import iniciar

ARGS = ArgsReserva(
    sala="sala-garagem",
    inicio="2026-11-03T14:00:00-03:00",
    fim="2026-11-03T15:00:00-03:00",
    responsavel="Marty",
)


def _pausa(request_state: str = "estado-opaco") -> TaskPausada:
    return TaskPausada(
        pendencia=PendenciaMRTR(
            chave="escolha_de_sala",
            campo="sala",
            alternativas=("sala-fusca", "sala-mirante"),
            request_state=request_state,
        ),
        args=ARGS,
        trace=iniciar(None),
    )


def test_task_sem_pausa_nao_tem_pendencia() -> None:
    assert Pendencias().obter("task-1") is None


def test_guarda_e_obtem_por_task_id() -> None:
    pendencias = Pendencias()
    pausa = _pausa()
    pendencias.guardar("task-1", pausa)
    assert pendencias.obter("task-1") == pausa


def test_isola_tasks_diferentes() -> None:
    pendencias = Pendencias()
    pendencias.guardar("task-a", _pausa("estado-a"))
    pendencias.guardar("task-b", _pausa("estado-b"))
    pausa_a, pausa_b = pendencias.obter("task-a"), pendencias.obter("task-b")
    assert pausa_a is not None and pausa_a.pendencia.request_state == "estado-a"
    assert pausa_b is not None and pausa_b.pendencia.request_state == "estado-b"


def test_guardar_de_novo_substitui_a_pausa() -> None:
    pendencias = Pendencias()
    pendencias.guardar("task-1", _pausa("antigo"))
    pendencias.guardar("task-1", _pausa("novo"))
    pausa = pendencias.obter("task-1")
    assert pausa is not None and pausa.pendencia.request_state == "novo"


def test_remover_apaga_e_tolera_task_ausente() -> None:
    pendencias = Pendencias()
    pendencias.guardar("task-1", _pausa())
    pendencias.remover("task-1")
    pendencias.remover("task-1")
    assert pendencias.obter("task-1") is None
