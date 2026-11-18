"""CT-02: controle de acesso por perfil (CA-02), verificado no servidor."""


def test_anonimo_e_enviado_para_o_login(client):
    resposta = client.get("/admin/")

    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]


def test_colaborador_nao_acessa_area_admin_digitando_a_url(entrar, client):
    entrar("1001", "colab123")

    resposta = client.get("/admin/")

    assert resposta.status_code == 403


def test_colaborador_nao_ve_link_para_area_admin(entrar, client):
    entrar("1001", "colab123")

    assert "Área do administrador" not in client.get("/").get_data(as_text=True)


def test_acesso_negado_fica_registrado_no_log(entrar, client, consulta):
    entrar("1001", "colab123")
    client.get("/admin/")

    acoes = [linha["acao"] for linha in consulta("SELECT acao FROM log ORDER BY id")]

    assert "acesso_negado" in acoes


def test_administrador_acessa_area_admin(entrar, client):
    entrar("9001", "admin123")

    resposta = client.get("/admin/")

    assert resposta.status_code == 200


def test_pagina_inexistente_devolve_404(client):
    assert client.get("/nao-existe").status_code == 404
