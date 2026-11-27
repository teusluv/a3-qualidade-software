"""Contas: desativar, reativar, excluir e trocar a própria senha."""

import sqlite3

import pytest

from app.db import get_db, migrar_banco

NOVA = {"matricula": "2001", "nome": "Maria da Silva", "setor": "Farmácia", "perfil": "colaborador", "senha": "senha1234"}


@pytest.fixture
def admin(app):
    cliente = app.test_client()
    cliente.post("/login", data={"matricula": "9001", "senha": "admin123"})
    return cliente


def _id(app, matricula):
    with app.app_context():
        return get_db().execute("SELECT id FROM usuario WHERE matricula = ?", (matricula,)).fetchone()["id"]


# ---------- desativar e reativar ----------


def test_conta_desativada_nao_consegue_entrar_e_a_mensagem_nao_revela_o_motivo(admin, app):
    admin.post(f"/admin/usuarios/{_id(app, '1002')}/desativar")

    resposta = app.test_client().post("/login", data={"matricula": "1002", "senha": "colab123"})

    assert resposta.status_code == 401
    assert "Matrícula ou senha inválidas" in resposta.get_data(as_text=True)
    assert "desativ" not in resposta.get_data(as_text=True).lower()


def test_quem_ja_estava_logado_perde_o_acesso_na_proxima_requisicao(admin, app):
    colaborador = app.test_client()
    colaborador.post("/login", data={"matricula": "1002", "senha": "colab123"})
    assert colaborador.get("/cursos").status_code == 200

    admin.post(f"/admin/usuarios/{_id(app, '1002')}/desativar")

    resposta = colaborador.get("/cursos")
    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]


def test_reativar_devolve_o_acesso(admin, app):
    uid = _id(app, "1002")
    admin.post(f"/admin/usuarios/{uid}/desativar")
    admin.post(f"/admin/usuarios/{uid}/reativar")

    resposta = app.test_client().post("/login", data={"matricula": "1002", "senha": "colab123"})

    assert resposta.status_code == 302


def test_desativar_preserva_o_historico_e_o_certificado_continua_valido(admin, app, id_curso, aprovar_por_sql, consulta):
    aprovar_por_sql("1001", "A", nota=90)
    colaborador = app.test_client()
    colaborador.post("/login", data={"matricula": "1001", "senha": "colab123"})
    colaborador.post(f"/cursos/{id_curso('A')}/certificado")
    codigo = consulta("SELECT codigo FROM certificado")[0]["codigo"]

    admin.post(f"/admin/usuarios/{_id(app, '1001')}/desativar")

    assert consulta("SELECT COUNT(*) AS n FROM certificado")[0]["n"] == 1
    assert consulta("SELECT COUNT(*) AS n FROM inscricao")[0]["n"] == 1
    assert "Autêntico" in app.test_client().get(f"/verificar?codigo={codigo}").get_data(as_text=True)
    assert "Carla Mendes Lima" in admin.get(f"/admin/cursos/{id_curso('A')}").get_data(as_text=True)


def test_admin_nao_desativa_a_propria_conta(admin, app, consulta):
    resposta = admin.post(f"/admin/usuarios/{_id(app, '9001')}/desativar", follow_redirects=True)

    assert "própria conta" in resposta.get_data(as_text=True)
    assert consulta("SELECT ativo FROM usuario WHERE matricula = '9001'")[0]["ativo"] == 1


def test_nao_desativa_o_ultimo_administrador_ativo(admin, app, consulta):
    admin.post("/admin/usuarios/", data={**NOVA, "perfil": "administrador", "matricula": "9002"})
    segundo = app.test_client()
    segundo.post("/login", data={"matricula": "9002", "senha": "senha1234"})

    segundo.post(f"/admin/usuarios/{_id(app, '9001')}/desativar")  # há 2 ativos: pode
    assert consulta("SELECT ativo FROM usuario WHERE matricula = '9001'")[0]["ativo"] == 0

    resposta = segundo.post(f"/admin/usuarios/{_id(app, '9002')}/desativar")  # a própria conta
    assert consulta("SELECT ativo FROM usuario WHERE matricula = '9002'")[0]["ativo"] == 1
    assert resposta.status_code == 302


def test_nao_desativa_o_ultimo_administrador_por_outro_admin_desativado(admin, app, consulta):
    """Com 9001 sozinho como administrador ativo, ele não pode ser desativado por ninguém."""
    from app.services import usuarios

    with app.app_context():
        db = get_db()
        with pytest.raises(usuarios.ContaInvalidaError, match="pelo menos um administrador"):
            usuarios.alterar_situacao(db, _id(app, "9001"), ativar=False, ator_id=999)


def test_desativar_e_reativar_ficam_registrados(admin, app, consulta):
    uid = _id(app, "1002")
    admin.post(f"/admin/usuarios/{uid}/desativar")
    admin.post(f"/admin/usuarios/{uid}/reativar")

    acoes = [r["acao"] for r in consulta("SELECT acao FROM log")]

    assert "usuario_desativar" in acoes
    assert "usuario_reativar" in acoes


def test_lista_mostra_a_situacao(admin, app):
    admin.post(f"/admin/usuarios/{_id(app, '1002')}/desativar")

    pagina = admin.get("/admin/usuarios/").get_data(as_text=True)

    assert "desativada" in pagina
    assert "Reativar" in pagina


# ---------- excluir ----------


def test_exclui_conta_sem_historico(admin, app, consulta):
    admin.post("/admin/usuarios/", data=NOVA)

    resposta = admin.post(f"/admin/usuarios/{_id(app, '2001')}/excluir")

    assert resposta.status_code == 302
    assert consulta("SELECT COUNT(*) AS n FROM usuario WHERE matricula = '2001'")[0]["n"] == 0


def test_nao_exclui_conta_com_historico(admin, app, consulta):
    novo = app.test_client()
    admin.post("/admin/usuarios/", data=NOVA)
    novo.post("/login", data={"matricula": "2001", "senha": "senha1234"})  # gera evento no log

    resposta = admin.post(f"/admin/usuarios/{_id(app, '2001')}/excluir", follow_redirects=True)

    assert "tem histórico" in resposta.get_data(as_text=True)
    assert consulta("SELECT COUNT(*) AS n FROM usuario WHERE matricula = '2001'")[0]["n"] == 1


def test_botao_excluir_so_aparece_para_conta_sem_historico(admin, app):
    admin.post("/admin/usuarios/", data=NOVA)  # conta nova, sem histórico
    app.test_client().post("/login", data={"matricula": "1002", "senha": "colab123"})  # 1002 passa a ter evento

    pagina = admin.get("/admin/usuarios/").get_data(as_text=True)
    linhas = {m: pagina.split(f"<td>{m}</td>")[1].split("</tr>")[0] for m in ("1001", "1002", "2001", "9001")}

    assert 'btn-outline-danger btn-sm">Excluir<' in linhas["1001"]  # nunca fez nada
    assert 'btn-outline-danger btn-sm">Excluir<' in linhas["2001"]  # recém-criada
    assert 'btn-outline-danger btn-sm">Excluir<' not in linhas["1002"]  # já tem evento
    assert 'btn-outline-danger btn-sm">Excluir<' not in linhas["9001"]  # administrador logado


def test_admin_nao_exclui_a_propria_conta(admin, app, consulta):
    admin.post(f"/admin/usuarios/{_id(app, '9001')}/excluir")

    assert consulta("SELECT COUNT(*) AS n FROM usuario WHERE matricula = '9001'")[0]["n"] == 1


def test_conta_inexistente_da_404(admin):
    assert admin.post("/admin/usuarios/99999/desativar").status_code == 404
    assert admin.post("/admin/usuarios/99999/reativar").status_code == 404
    assert admin.post("/admin/usuarios/99999/excluir").status_code == 404


def test_colaborador_nao_desativa_nem_exclui(entrar, client, app, consulta):
    entrar("1001", "colab123")
    alvo = _id(app, "1002")

    respostas = [client.post(f"/admin/usuarios/{alvo}/{acao}") for acao in ("desativar", "reativar", "excluir")]

    assert [r.status_code for r in respostas] == [403, 403, 403]
    assert consulta("SELECT ativo FROM usuario WHERE matricula = '1002'")[0]["ativo"] == 1


# ---------- trocar a própria senha ----------


def test_pagina_de_troca_de_senha_exige_login(app):
    assert app.test_client().get("/conta/senha").status_code == 302


def test_nome_no_menu_leva_para_a_troca_de_senha(entrar, client):
    entrar("1001", "colab123")

    assert 'href="/conta/senha"' in client.get("/cursos").get_data(as_text=True)


def test_colaborador_troca_a_propria_senha(entrar, client, app):
    entrar("1001", "colab123")

    resposta = client.post("/conta/senha", data={"senha_atual": "colab123", "senha_nova": "novaSenha77", "senha_confirmacao": "novaSenha77"})

    assert resposta.status_code == 302
    assert app.test_client().post("/login", data={"matricula": "1001", "senha": "colab123"}).status_code == 401
    assert app.test_client().post("/login", data={"matricula": "1001", "senha": "novaSenha77"}).status_code == 302


@pytest.mark.parametrize(
    ("dados", "trecho"),
    [
        ({"senha_atual": "errada123", "senha_nova": "novaSenha77", "senha_confirmacao": "novaSenha77"}, "Senha atual"),
        ({"senha_atual": "colab123", "senha_nova": "curta1", "senha_confirmacao": "curta1"}, "Senha:"),
        ({"senha_atual": "colab123", "senha_nova": "colab123", "senha_confirmacao": "colab123"}, "diferente da atual"),
        ({"senha_atual": "colab123", "senha_nova": "novaSenha77", "senha_confirmacao": "outraSenha77"}, "Confirmação"),
    ],
)
def test_troca_invalida_nao_altera_a_senha(entrar, client, app, dados, trecho):
    entrar("1001", "colab123")

    resposta = client.post("/conta/senha", data=dados)

    assert resposta.status_code == 400
    assert trecho in resposta.get_data(as_text=True)
    assert app.test_client().post("/login", data={"matricula": "1001", "senha": "colab123"}).status_code == 302


def test_troca_fica_registrada_sem_guardar_senha(entrar, client, consulta):
    entrar("1001", "colab123")
    client.post("/conta/senha", data={"senha_atual": "colab123", "senha_nova": "novaSenha77", "senha_confirmacao": "novaSenha77"})

    logs = " ".join(str(tuple(r)) for r in consulta("SELECT * FROM log"))

    assert "senha_alterada" in logs
    assert "novaSenha77" not in logs
    assert "colab123" not in logs


# ---------- migração de banco antigo ----------


def test_banco_sem_a_coluna_ativo_e_migrado_e_as_contas_continuam_ativas(tmp_path):
    caminho = tmp_path / "antigo.db"
    conexao = sqlite3.connect(caminho)
    conexao.row_factory = sqlite3.Row
    conexao.execute("CREATE TABLE usuario (id INTEGER PRIMARY KEY, matricula TEXT, nome TEXT, senha_hash TEXT, perfil TEXT, setor TEXT)")
    conexao.execute("INSERT INTO usuario VALUES (1, '1001', 'Antiga', 'x', 'colaborador', 'TI')")
    conexao.commit()

    migrar_banco(conexao)
    migrar_banco(conexao)  # rodar de novo não pode falhar

    linha = conexao.execute("SELECT ativo FROM usuario").fetchone()
    assert linha["ativo"] == 1
    conexao.close()
