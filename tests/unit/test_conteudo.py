"""Caixa-branca: validações de atividade, questão, link e a paginação."""

import pytest

from app.services.conteudo import validar_link, validar_questao, validar_titulo_atividade
from app.services.logs import paginar

QUESTAO = {
    "enunciado": "Qual é a resposta correta?", "opcao_a": "Um", "opcao_b": "Dois",
    "opcao_c": "Três", "opcao_d": "Quatro", "correta": "c",
}


# ---------- links de vídeo ----------


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=abc123",
        "http://intranet.hospital.local/video",
        "https://exemplo.com/a?b=1&c=2#t",
    ],
)
def test_links_http_e_https_sao_aceitos(url):
    limpo, erros = validar_link("Aula 1", url)

    assert erros == []
    assert limpo["url"] == url


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)", "JAVASCRIPT:alert(1)", "data:text/html,<script>1</script>",
        "ftp://servidor/arquivo", "file:///etc/passwd", "exemplo.com/video", "//exemplo.com",
        "https://", "", "https://exemplo.com/com espaco", "https://exemplo.com/\nquebra",
        "https://exemplo.com/" + "a" * 500,
    ],
)
def test_links_perigosos_ou_incompletos_sao_recusados(url):
    _, erros = validar_link("Aula 1", url)

    assert any("endereço" in e for e in erros)


@pytest.mark.parametrize("titulo", ["", "ab", "x" * 101])
def test_titulo_do_link_invalido(titulo):
    _, erros = validar_link(titulo, "https://exemplo.com")

    assert any("título" in e for e in erros)


# ---------- atividades ----------


@pytest.mark.parametrize(
    ("titulo", "valido"),
    [("Leitura", True), ("ab", False), ("", False), ("x" * 101, False), (None, False)],
)
def test_titulo_da_atividade(titulo, valido):
    _, erros = validar_titulo_atividade(titulo)

    assert (erros == []) is valido


# ---------- questões ----------


def test_questao_valida():
    limpo, erros = validar_questao(QUESTAO)

    assert erros == []
    assert limpo["correta"] == "c"


def test_letra_da_resposta_certa_aceita_maiuscula():
    limpo, erros = validar_questao({**QUESTAO, "correta": "B"})

    assert erros == []
    assert limpo["correta"] == "b"


@pytest.mark.parametrize("correta", ["", "e", "ab", "1"])
def test_resposta_certa_invalida(correta):
    _, erros = validar_questao({**QUESTAO, "correta": correta})

    assert any("Resposta certa" in e for e in erros)


def test_opcoes_repetidas_sao_recusadas_mesmo_com_caixa_diferente():
    _, erros = validar_questao({**QUESTAO, "opcao_b": "um"})

    assert any("diferentes" in e for e in erros)


@pytest.mark.parametrize("campo", ["opcao_a", "opcao_b", "opcao_c", "opcao_d"])
def test_opcao_vazia_e_recusada(campo):
    _, erros = validar_questao({**QUESTAO, campo: "  "})

    assert any(campo[-1].upper() in e for e in erros)


@pytest.mark.parametrize("enunciado", ["", "abc", "x" * 301])
def test_enunciado_invalido(enunciado):
    _, erros = validar_questao({**QUESTAO, "enunciado": enunciado})

    assert any("Pergunta" in e for e in erros)


# ---------- paginação ----------


@pytest.mark.parametrize(
    ("total", "pagina", "esperado"),
    [
        (0, 1, (1, 1, 0)),  # sem eventos: 1 página vazia
        (20, 1, (1, 1, 0)),  # exatamente uma página
        (21, 1, (1, 2, 0)),
        (21, 2, (2, 2, 20)),
        (45, 3, (3, 3, 40)),
        (45, 99, (3, 3, 40)),  # página além do fim vira a última
        (45, 0, (1, 3, 0)),  # página zero vira a primeira
        (45, -5, (1, 3, 0)),
    ],
)
def test_paginar(total, pagina, esperado):
    assert paginar(total, pagina, 20) == esperado
