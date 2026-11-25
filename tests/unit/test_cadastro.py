"""Caixa-branca: validação do cadastro de curso (RF-09, RN-01)."""

import pytest

from app.services.cadastro import validar_curso

SETORES = {"Enfermagem", "Farmácia", "TI"}
VALIDO = {
    "codigo": "e1", "titulo": "Biossegurança Básica", "carga_horaria": "6", "nota_minima": "75",
    "setor": "Enfermagem", "status": "ativo", "data_inicio": "2026-12-01", "data_fim": "2027-12-01",
    "obrigatorio": "on",
}


def _com(**mudancas):
    return {**VALIDO, **mudancas}


def test_dados_validos_geram_curso_limpo_sem_erros():
    limpo, erros = validar_curso(VALIDO, SETORES)

    assert erros == []
    assert limpo["codigo"] == "E1"  # sempre em maiúsculas
    assert limpo["nota_minima"] == 75
    assert limpo["obrigatorio"] == 1
    assert limpo["setor"] == "Enfermagem"


def test_setor_vazio_significa_todos_os_setores():
    limpo, erros = validar_curso(_com(setor=""), SETORES)

    assert erros == []
    assert limpo["setor"] is None


def test_curso_nao_obrigatorio_quando_a_caixa_nao_vem_marcada():
    dados = {k: v for k, v in VALIDO.items() if k != "obrigatorio"}

    limpo, _ = validar_curso(dados, SETORES)

    assert limpo["obrigatorio"] == 0


@pytest.mark.parametrize("nota", ["69", "0", "101", "abc", "", "70.5"])
def test_nota_minima_fora_de_70_a_100_e_recusada(nota):
    _, erros = validar_curso(_com(nota_minima=nota), SETORES)

    assert any("Nota mínima" in e for e in erros)


@pytest.mark.parametrize("nota", ["70", "100"])
def test_nota_minima_nos_limites_e_aceita(nota):
    _, erros = validar_curso(_com(nota_minima=nota), SETORES)

    assert erros == []


@pytest.mark.parametrize("codigo", ["", "A B", "ABCDEFGHIJK", "A-1", "<b>"])
def test_codigo_invalido(codigo):
    _, erros = validar_curso(_com(codigo=codigo), SETORES)

    assert any("Código" in e for e in erros)


@pytest.mark.parametrize("titulo", ["", "ab", "x" * 121])
def test_titulo_invalido(titulo):
    _, erros = validar_curso(_com(titulo=titulo), SETORES)

    assert any("Título" in e for e in erros)


@pytest.mark.parametrize("carga", ["0", "201", "-1", "x", ""])
def test_carga_horaria_invalida(carga):
    _, erros = validar_curso(_com(carga_horaria=carga), SETORES)

    assert any("Carga horária" in e for e in erros)


def test_periodo_com_fim_antes_do_inicio():
    _, erros = validar_curso(_com(data_inicio="2026-12-10", data_fim="2026-12-01"), SETORES)

    assert any("anterior" in e for e in erros)


@pytest.mark.parametrize("data", ["", "31/12/2026", "2026-13-40"])
def test_data_invalida(data):
    _, erros = validar_curso(_com(data_inicio=data), SETORES)

    assert any("Período" in e for e in erros)


def test_setor_inexistente_e_status_arquivado_na_criacao_sao_recusados():
    _, erros = validar_curso(_com(setor="Marte", status="arquivado"), SETORES)

    assert any("Setor" in e for e in erros)
    assert any("Situação" in e for e in erros)


def test_varios_erros_sao_devolvidos_de_uma_vez():
    _, erros = validar_curso({}, SETORES)

    assert len(erros) >= 5
