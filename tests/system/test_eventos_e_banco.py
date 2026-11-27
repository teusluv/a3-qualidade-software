"""Eventos paginados (limite de 20) e visualização somente leitura do banco."""

import pytest


@pytest.fixture
def admin(app):
    cliente = app.test_client()
    cliente.post("/login", data={"matricula": "9001", "senha": "admin123"})
    return cliente


@pytest.fixture
def com_50_eventos(executar):
    for n in range(50):
        executar(
            "INSERT INTO log (usuario_id, acao, detalhe, criado_em) VALUES (NULL, ?, ?, ?)",
            (f"evento_{n:02d}", f"detalhe {n}", f"2026-11-01T10:{n:02d}:00"),
        )


def _linhas(pagina_html: str) -> int:
    corpo = pagina_html.split("<tbody>")[1].split("</tbody>")[0]
    return corpo.count("<tr>")


# ---------- eventos ----------


def test_painel_mostra_so_os_20_eventos_mais_recentes(admin, com_50_eventos):
    pagina = admin.get("/admin/").get_data(as_text=True)
    # a tabela de eventos é a última tabela do painel
    tabela_de_eventos = pagina.split("Últimos eventos registrados")[1]

    assert _linhas(tabela_de_eventos) == 20
    assert "Mostrando os 20 mais recentes de 51" in pagina  # 50 criados + o login do admin
    assert "Ver todos, por página" in pagina


def test_eventos_aparecem_do_mais_novo_para_o_mais_antigo(admin, com_50_eventos):
    pagina = admin.get("/admin/eventos").get_data(as_text=True)

    assert pagina.index("evento_49") < pagina.index("evento_40")
    assert "evento_00" not in pagina  # o mais antigo está em outra página


def test_pagina_de_eventos_tem_20_por_pagina_e_navegacao(admin, com_50_eventos):
    p1 = admin.get("/admin/eventos").get_data(as_text=True)
    p2 = admin.get("/admin/eventos?pagina=2").get_data(as_text=True)
    p3 = admin.get("/admin/eventos?pagina=3").get_data(as_text=True)

    assert (_linhas(p1), _linhas(p2), _linhas(p3)) == (20, 20, 11)
    assert "Página 1 de 3" in p1
    assert "Próxima" in p1
    assert "Página 3 de 3" in p3


def test_nada_e_apagado_o_mais_antigo_continua_na_ultima_pagina(admin, com_50_eventos):
    ultima = admin.get("/admin/eventos?pagina=3").get_data(as_text=True)

    assert "evento_00" in ultima


@pytest.mark.parametrize("pagina", ["0", "-3", "999", "abc", ""])
def test_pagina_invalida_nao_quebra(admin, com_50_eventos, pagina):
    resposta = admin.get(f"/admin/eventos?pagina={pagina}")

    assert resposta.status_code == 200
    assert "Página" in resposta.get_data(as_text=True)


def test_so_o_administrador_ve_os_eventos(entrar, client):
    entrar("1001", "colab123")

    assert client.get("/admin/eventos").status_code == 403


# ---------- banco de dados ----------


def test_pagina_do_banco_mostra_onde_fica_e_as_tabelas(admin, app):
    pagina = admin.get("/admin/banco").get_data(as_text=True)

    assert app.config["DATABASE"] in pagina
    assert "SQLite" in pagina
    for tabela in ("usuario", "curso", "atividade", "questao", "inscricao", "progresso",
                   "tentativa", "certificado", "log", "material", "link_curso"):
        assert f">{tabela}</a>" in pagina


def test_banco_mostra_a_contagem_de_registros(admin):
    pagina = admin.get("/admin/banco").get_data(as_text=True)

    linha_usuario = pagina.split(">usuario</a>")[1].split("</tr>")[0]
    assert "<td>3</td>" in linha_usuario  # 3 usuários de demonstração


def test_tabela_mostra_linhas_mas_oculta_o_hash_da_senha(admin):
    pagina = admin.get("/admin/banco/usuario").get_data(as_text=True)

    assert "Carla Mendes Lima" in pagina
    assert "senha_hash" in pagina  # o nome da coluna aparece
    assert "(oculto)" in pagina  # o valor, não
    assert "scrypt" not in pagina
    assert "pbkdf2" not in pagina


def test_tabela_grande_e_paginada(admin, executar):
    for n in range(45):
        executar("INSERT INTO log (usuario_id, acao, detalhe, criado_em) VALUES (NULL, 'x', ?, '2026-11-01T10:00:00')", (str(n),))

    p1 = admin.get("/admin/banco/log").get_data(as_text=True)
    p3 = admin.get("/admin/banco/log?pagina=3").get_data(as_text=True)

    assert "Página 1 de" in p1
    assert _linhas(p1) == 20
    assert "Página 3 de" in p3


@pytest.mark.parametrize("nome", ["nao_existe", "usuario;DROP TABLE usuario", "usuario--", "sqlite_master", '"usuario"'])
def test_nome_de_tabela_invalido_ou_perigoso_da_404_e_nada_acontece(admin, consulta, nome):
    resposta = admin.get(f"/admin/banco/{nome}")

    assert resposta.status_code == 404
    assert consulta("SELECT COUNT(*) AS n FROM usuario")[0]["n"] == 3


def test_banco_e_somente_leitura(admin):
    assert admin.post("/admin/banco/usuario").status_code == 405
    assert admin.post("/admin/banco", data={"sql": "DELETE FROM usuario"}).status_code == 405


def test_so_o_administrador_ve_o_banco(entrar, client, app):
    entrar("1001", "colab123")

    assert client.get("/admin/banco").status_code == 403
    assert client.get("/admin/banco/usuario").status_code == 403
    assert app.test_client().get("/admin/banco").status_code == 302  # anônimo vai ao login
