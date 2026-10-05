import re

from agente_salas.domain.trace import TraceContext, iniciar

PADRAO_TRACEPARENT = re.compile(r"^00-[0-9a-f]{32}-[0-9a-f]{16}-01$")


def test_iniciar_sem_header_gera_trace_id_e_span_novos() -> None:
    contexto = iniciar(None)
    assert PADRAO_TRACEPARENT.match(contexto.traceparent)


def test_iniciar_com_header_valido_preserva_trace_id_com_span_novo() -> None:
    recebido = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
    contexto = iniciar(recebido)
    assert contexto.trace_id == "4bf92f3577b34da6a3ce929d0e0e4736"
    assert contexto.span_id != "00f067aa0ba902b7"
    assert PADRAO_TRACEPARENT.match(contexto.traceparent)


def test_iniciar_com_header_invalido_gera_contexto_novo() -> None:
    contexto = iniciar("lixo-sem-formato")
    assert PADRAO_TRACEPARENT.match(contexto.traceparent)


def test_com_novo_span_preserva_trace_id_e_troca_span() -> None:
    original = iniciar(None)
    seguinte = original.com_novo_span()
    assert seguinte.trace_id == original.trace_id
    assert seguinte.span_id != original.span_id


def test_duas_chamadas_a_iniciar_geram_trace_ids_diferentes() -> None:
    primeiro = iniciar(None)
    segundo = iniciar(None)
    assert primeiro.trace_id != segundo.trace_id


def test_trace_context_e_imutavel() -> None:
    contexto = TraceContext(trace_id="a" * 32, span_id="b" * 16)
    assert contexto.traceparent == f"00-{'a' * 32}-{'b' * 16}-01"
