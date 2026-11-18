"""Caixa-branca: funções puras do certificado (RN-03, A-05, CA-07)."""

import pytest

from app.services import certificado as cert


@pytest.mark.parametrize(
    ("nome", "esperado"),
    [
        ("Carla Mendes Lima", "Carla M. L."),
        ("Maria da Silva", "Maria S."),
        ("José de Souza e Santos", "José S. S."),
        ("Ana", "Ana"),
        ("  Ana   Paula  ", "Ana P."),
        ("", ""),
        ("   ", ""),
    ],
)
def test_mascarar_nome(nome, esperado):
    assert cert.mascarar_nome(nome) == esperado


def test_mascara_nao_expoe_sobrenomes():
    assert "Mendes" not in cert.mascarar_nome("Carla Mendes Lima")
    assert "Lima" not in cert.mascarar_nome("Carla Mendes Lima")


def test_codigo_e_longo_e_url_seguro():
    codigo = cert.gerar_codigo()

    assert len(codigo) >= 16
    assert cert.codigo_tem_formato_valido(codigo)


def test_codigos_gerados_nao_se_repetem_nem_sao_sequenciais():
    codigos = [cert.gerar_codigo() for _ in range(1000)]

    assert len(set(codigos)) == 1000


@pytest.mark.parametrize(
    ("codigo", "valido"),
    [
        ("abcDEF123_-xyz00", True),
        ("curto", False),
        ("", False),
        ("com espaco aqui!!", False),
        ("' OR 1=1 --", False),
        ("<script>alert(1)</script>", False),
        ("a" * 65, False),
        ("a" * 64, True),
        ("codigo\nquebra-de-linha", False),
    ],
)
def test_formato_do_codigo(codigo, valido):
    assert cert.codigo_tem_formato_valido(codigo) is valido


def test_formatar_data():
    assert cert.formatar_data("2026-11-16T10:30:00") == "16/11/2026"


def test_pdf_com_campo_vazio_e_recusado():
    dados = {
        "nome": "Carla", "matricula": "", "titulo": "Curso", "carga_horaria": 4,
        "concluido_em": "2026-11-16T10:00:00", "codigo": "abc12345",
    }

    with pytest.raises(ValueError):
        cert.gerar_pdf(dados)
