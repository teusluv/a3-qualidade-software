"""Caixa-branca (CT-05, CT-17): funções puras de nota, aprovação e tentativas."""

import pytest

from app.services import avaliacao as av

# ---------- calcular_nota ----------


@pytest.mark.parametrize(
    ("acertos", "total", "esperado"),
    [(0, 10, 0), (6, 10, 60), (7, 10, 70), (8, 10, 80), (10, 10, 100), (2, 3, 66), (1, 3, 33)],
)
def test_calcular_nota(acertos, total, esperado):
    assert av.calcular_nota(acertos, total) == esperado


def test_calcular_nota_trunca_e_nao_arredonda_para_cima():
    # 199/200 = 99,5%: não pode virar 100%
    assert av.calcular_nota(199, 200) == 99


@pytest.mark.parametrize(("acertos", "total"), [(1, 0), (1, -5), (-1, 10), (11, 10)])
def test_calcular_nota_rejeita_valores_invalidos(acertos, total):
    with pytest.raises(ValueError):
        av.calcular_nota(acertos, total)


# ---------- nota mínima e aprovação (RN-01, CA-05) ----------


@pytest.mark.parametrize(
    ("minimo_do_curso", "esperado"), [(50, 70), (69, 70), (70, 70), (80, 80), (100, 100)]
)
def test_nota_minima_nunca_fica_abaixo_de_70(minimo_do_curso, esperado):
    assert av.nota_minima_efetiva(minimo_do_curso) == esperado


@pytest.mark.parametrize(
    ("nota", "minimo", "esperado"),
    [
        (69, 70, False),  # limite inferior
        (70, 70, True),  # no limite aprova
        (71, 70, True),
        (79, 80, False),  # curso B
        (80, 80, True),
        (81, 80, True),
        (0, 70, False),
        (100, 100, True),
        (75, 60, True),  # curso configurado abaixo de 70 usa 70
        (65, 60, False),
    ],
)
def test_aprovado_nos_limites(nota, minimo, esperado):
    assert av.aprovado(nota, minimo) is esperado


def test_ca05_curso_a_e_curso_b_com_10_questoes():
    # Curso A (70%): 7 acertos aprova, 6 reprova
    assert av.aprovado(av.calcular_nota(7, 10), 70) is True
    assert av.aprovado(av.calcular_nota(6, 10), 70) is False
    # Curso B (80%): 7 reprova, 8 aprova
    assert av.aprovado(av.calcular_nota(7, 10), 80) is False
    assert av.aprovado(av.calcular_nota(8, 10), 80) is True


# ---------- correção ----------

GABARITO = {1: "a", 2: "b", 3: "c"}


def test_contar_acertos_todos_certos():
    assert av.contar_acertos({1: "a", 2: "b", 3: "c"}, GABARITO) == 3


def test_contar_acertos_parcial():
    assert av.contar_acertos({1: "a", 2: "d", 3: "c"}, GABARITO) == 2


def test_questao_sem_resposta_conta_como_erro():
    assert av.contar_acertos({1: "a"}, GABARITO) == 1


def test_opcao_invalida_conta_como_erro():
    assert av.contar_acertos({1: "z", 2: "", 3: "C"}, GABARITO) == 0


def test_resposta_para_questao_fora_do_gabarito_e_ignorada():
    assert av.contar_acertos({1: "a", 99: "a"}, GABARITO) == 1


def test_sem_respostas_nenhum_acerto():
    assert av.contar_acertos({}, GABARITO) == 0


# ---------- tentativas (RF-06, A-02, A-07) ----------


@pytest.mark.parametrize(
    ("realizadas", "esperado"), [(0, True), (1, True), (2, True), (3, False), (4, False)]
)
def test_pode_tentar(realizadas, esperado):
    assert av.pode_tentar(realizadas) is esperado


@pytest.mark.parametrize(("realizadas", "restantes"), [(0, 3), (2, 1), (3, 0), (5, 0)])
def test_tentativas_restantes(realizadas, restantes):
    assert av.tentativas_restantes(realizadas) == restantes


def test_maior_nota_ca06_notas_60_80_70():
    assert av.maior_nota([60, 80, 70]) == 80


def test_maior_nota_sem_tentativas():
    assert av.maior_nota([]) is None


def test_maior_nota_aceita_qualquer_iteravel():
    assert av.maior_nota(n for n in (10, 90, 50)) == 90


# ---------- atividades e progresso (A-06, CA-04) ----------


@pytest.mark.parametrize(
    ("concluidas", "total", "esperado"),
    [(4, 4, True), (3, 4, False), (0, 4, False), (0, 0, False)],
)
def test_atividades_concluidas_exige_100_por_cento(concluidas, total, esperado):
    assert av.atividades_concluidas(concluidas, total) is esperado


def test_atividades_concluidas_com_percentual_configuravel():
    assert av.atividades_concluidas(3, 4, percentual=75) is True
    assert av.atividades_concluidas(2, 4, percentual=75) is False


@pytest.mark.parametrize(
    ("concluidas", "total", "esperado"), [(2, 4, 50), (0, 4, 0), (4, 4, 100), (1, 3, 33), (0, 0, 0)]
)
def test_progresso_percentual(concluidas, total, esperado):
    assert av.progresso_percentual(concluidas, total) == esperado


# ---------- elegibilidade do certificado (RN-02, CA-09) ----------


@pytest.mark.parametrize(
    ("melhor", "minimo", "atividades_ok", "esperado"),
    [
        (80, 70, True, True),
        (70, 70, True, True),
        (69, 70, True, False),  # reprovado
        (90, 70, False, False),  # atividades incompletas
        (None, 70, True, False),  # nunca avaliou
        (None, 70, False, False),
        (79, 80, True, False),
    ],
)
def test_elegivel_para_certificado(melhor, minimo, atividades_ok, esperado):
    assert av.elegivel_para_certificado(melhor, minimo, atividades_ok) is esperado
