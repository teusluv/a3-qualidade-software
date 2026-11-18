"""CT-11 e CT-12: consulta pública (CA-11, CA-12, RN-03, RNF-07)."""

import pytest


@pytest.fixture
def codigo_valido(entrar, client, id_curso, aprovar_por_sql, consulta):
    aprovar_por_sql("1001", "A")
    entrar("1001", "colab123")
    client.post(f"/cursos/{id_curso('A')}/certificado")
    client.post("/logout")
    return consulta("SELECT codigo FROM certificado")[0]["codigo"]


def test_ct11_codigo_valido_mostra_autentico_curso_e_data(app, codigo_valido):
    anonimo = app.test_client()  # sem login

    resposta = anonimo.get(f"/verificar?codigo={codigo_valido}")
    pagina = resposta.get_data(as_text=True)

    assert resposta.status_code == 200
    assert "Autêntico" in pagina
    assert "Segurança do Paciente" in pagina
    assert "Data de conclusão" in pagina


def test_ct11_codigo_inexistente(client):
    resposta = client.get("/verificar?codigo=CodigoQueNaoExiste123")

    assert resposta.status_code == 404
    assert "Certificado não encontrado" in resposta.get_data(as_text=True)


def test_ct11_campo_vazio_e_validado(client):
    resposta = client.get("/verificar?codigo=")

    assert resposta.status_code == 400
    assert "Informe o código" in resposta.get_data(as_text=True)


def test_pagina_inicial_da_consulta_nao_exige_login(client):
    assert client.get("/verificar").status_code == 200


def test_ct12_resposta_nao_expoe_dados_pessoais(app, codigo_valido):
    html = app.test_client().get(f"/verificar?codigo={codigo_valido}").get_data(as_text=True)
    conteudo = html[html.index("<main") : html.index("</main>")]  # só o conteúdo da página

    assert "Carla M. L." in conteudo  # nome só mascarado
    for proibido in ("Mendes", "Lima", "1001", "colab123", "@", "CPF", "senha"):
        assert proibido not in conteudo


@pytest.mark.parametrize(
    "entrada",
    [
        "'",
        "' OR 1=1 --",
        "1' OR '1'='1",
        "<script>alert(1)</script>",
        '"><img src=x onerror=alert(1)>',
        "a" * 200,
    ],
)
def test_ct12_entradas_maliciosas_sao_tratadas_como_texto(client, consulta, entrada):
    resposta = client.get("/verificar", query_string={"codigo": entrada})
    pagina = resposta.get_data(as_text=True)

    assert resposta.status_code == 400
    assert "<script>alert" not in pagina
    assert "onerror" not in pagina
    assert entrada not in pagina  # a entrada nunca é devolvida na página
    assert consulta("SELECT COUNT(*) AS n FROM usuario")[0]["n"] == 3  # banco intacto
