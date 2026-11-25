"""Usabilidade: botões de voltar e limpeza dos campos quando o login falha."""

import pytest


def test_login_com_erro_limpa_matricula_e_senha(entrar):
    resposta = entrar("1001", "senha-errada-secreta")
    pagina = resposta.get_data(as_text=True)

    assert resposta.status_code == 401
    assert "senha-errada-secreta" not in pagina
    assert 'value="1001"' not in pagina  # a matrícula digitada também não volta
    assert 'name="matricula"' in pagina  # o formulário continua na tela, vazio


def test_login_com_matricula_inexistente_tambem_volta_vazio(entrar):
    pagina = entrar("matricula-que-nao-existe", "x").get_data(as_text=True)

    assert "matricula-que-nao-existe" not in pagina


def test_curso_tem_botao_voltar_para_o_catalogo(entrar, client, id_curso):
    entrar("1001", "colab123")

    pagina = client.get(f"/cursos/{id_curso('A')}").get_data(as_text=True)

    assert "Voltar aos cursos" in pagina
    assert 'href="/cursos"' in pagina


def test_avaliacao_tem_botao_voltar_para_o_curso(
    entrar, client, id_curso, concluir_todas
):
    entrar("1001", "colab123")
    curso = id_curso("A")
    client.post(f"/cursos/{curso}/iniciar")
    concluir_todas(curso)

    pagina = client.get(f"/cursos/{curso}/avaliacao").get_data(as_text=True)

    assert "Voltar ao curso" in pagina
    assert f'href="/cursos/{curso}"' in pagina


@pytest.mark.parametrize("caminho", ["/historico", "/admin/"])
def test_historico_e_admin_tem_botao_voltar(entrar, client, caminho):
    entrar("9001", "admin123")

    assert "Voltar aos cursos" in client.get(caminho).get_data(as_text=True)


def test_verificacao_publica_volta_para_o_login_quando_anonimo(client):
    pagina = client.get("/verificar").get_data(as_text=True)

    assert "Voltar ao login" in pagina


def test_verificacao_publica_volta_para_os_cursos_quando_logado(entrar, client):
    entrar("1001", "colab123")

    assert "Voltar aos cursos" in client.get("/verificar").get_data(as_text=True)


def test_pagina_de_erro_tem_botao_voltar_para_o_inicio(entrar, client):
    entrar("1001", "colab123")

    pagina = client.get("/admin/").get_data(as_text=True)  # 403

    assert "Voltar" in pagina
    assert 'href="/cursos"' in pagina
    assert "javascript:" not in pagina


def test_voltar_da_pagina_de_erro_usa_a_pagina_anterior_do_proprio_sistema(entrar, client):
    entrar("1001", "colab123")

    pagina = client.get("/admin/", headers={"Referer": "http://localhost/historico"})

    assert 'href="http://localhost/historico"' in pagina.get_data(as_text=True)


def test_voltar_da_pagina_de_erro_ignora_pagina_de_outro_site(entrar, client):
    entrar("1001", "colab123")

    pagina = client.get("/admin/", headers={"Referer": "http://site-malicioso.example/x"})

    texto = pagina.get_data(as_text=True)
    assert "site-malicioso" not in texto
    assert 'href="/cursos"' in texto
