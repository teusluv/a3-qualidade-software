"""Administração: criar contas e redefinir senhas."""

import pytest
from werkzeug.security import check_password_hash

NOVA = {"matricula": "2001", "nome": "Maria da Silva", "setor": "Farmácia", "perfil": "colaborador", "senha": "senha1234"}


@pytest.fixture
def admin(app):
    cliente = app.test_client()
    cliente.post("/login", data={"matricula": "9001", "senha": "admin123"})
    return cliente


def test_lista_mostra_as_contas_sem_expor_senhas(admin):
    pagina = admin.get("/admin/usuarios/").get_data(as_text=True)

    assert "Carla Mendes Lima" in pagina
    assert "1001" in pagina
    assert "scrypt" not in pagina
    assert "colab123" not in pagina


def test_painel_tem_atalho_para_as_contas(admin):
    assert "Contas de usuário" in admin.get("/admin/").get_data(as_text=True)


def test_formulario_explica_as_regras(admin):
    pagina = admin.get("/admin/usuarios/").get_data(as_text=True)

    assert "só números (3 a 10)" in pagina
    assert "sem repetir" in pagina
    assert "pelo menos uma letra e um número" in pagina


def test_criar_conta_e_a_pessoa_consegue_entrar(admin, app, consulta):
    resposta = admin.post("/admin/usuarios/", data=NOVA)

    assert resposta.status_code == 302
    linha = consulta("SELECT * FROM usuario WHERE matricula = '2001'")[0]
    assert (linha["nome"], linha["perfil"], linha["setor"]) == ("Maria da Silva", "colaborador", "Farmácia")
    novo = app.test_client()
    entrada = novo.post("/login", data={"matricula": "2001", "senha": "senha1234"})
    assert entrada.status_code == 302
    assert "Maria da Silva" in novo.get("/cursos").get_data(as_text=True)


def test_senha_fica_so_como_hash_e_nao_aparece_em_log_nem_na_tela(admin, consulta):
    resposta = admin.post("/admin/usuarios/", data=NOVA, follow_redirects=True)

    linha = consulta("SELECT senha_hash FROM usuario WHERE matricula = '2001'")[0]
    assert linha["senha_hash"] != "senha1234"
    assert check_password_hash(linha["senha_hash"], "senha1234")
    assert "senha1234" not in resposta.get_data(as_text=True)
    logs = " ".join(str(tuple(r)) for r in consulta("SELECT * FROM log"))
    assert "senha1234" not in logs
    assert "usuario_criado" in logs


def test_criar_administrador(admin, app):
    admin.post("/admin/usuarios/", data={**NOVA, "perfil": "administrador", "matricula": "9002"})
    outro = app.test_client()
    outro.post("/login", data={"matricula": "9002", "senha": "senha1234"})

    assert outro.get("/admin/").status_code == 200


def test_matricula_repetida_e_recusada(admin, consulta):
    resposta = admin.post("/admin/usuarios/", data={**NOVA, "matricula": "1001"})

    assert resposta.status_code == 400
    assert "já existe uma conta com esta matrícula" in resposta.get_data(as_text=True)
    assert consulta("SELECT COUNT(*) AS n FROM usuario")[0]["n"] == 3


@pytest.mark.parametrize(
    ("campo", "valor", "trecho"),
    [("matricula", "12", "Matrícula"), ("matricula", "abc", "Matrícula"), ("nome", "a", "Nome"),
     ("perfil", "root", "Perfil"), ("senha", "curta1", "Senha"), ("senha", "somenteletras", "Senha")],
)
def test_conta_invalida_nao_e_criada(admin, consulta, campo, valor, trecho):
    resposta = admin.post("/admin/usuarios/", data={**NOVA, campo: valor})

    assert resposta.status_code == 400
    assert trecho in resposta.get_data(as_text=True)
    assert consulta("SELECT COUNT(*) AS n FROM usuario")[0]["n"] == 3


def test_erro_mantem_o_que_foi_digitado_menos_a_senha(admin):
    resposta = admin.post("/admin/usuarios/", data={**NOVA, "nome": "Maria Digitada", "senha": "curta"})
    pagina = resposta.get_data(as_text=True)

    assert "Maria Digitada" in pagina
    assert "curta" not in pagina.replace("Senha inicial", "")  # a senha digitada não volta


def test_setor_novo_passa_a_valer_nos_cursos(admin, consulta):
    admin.post("/admin/usuarios/", data={**NOVA, "setor": "Laboratório"})

    resposta = admin.post("/admin/cursos", data={
        "codigo": "LAB1", "titulo": "Curso do Laboratório", "carga_horaria": "4", "nota_minima": "70",
        "setor": "Laboratório", "status": "ativo", "data_inicio": "2026-01-01", "data_fim": "2999-12-31"})

    assert resposta.status_code == 302
    assert consulta("SELECT setor FROM curso WHERE codigo = 'LAB1'")[0]["setor"] == "Laboratório"


def test_redefinir_senha_troca_o_acesso(admin, app):
    admin.post("/admin/usuarios/", data=NOVA)
    uid = app.test_client()  # sem login: só para conferir antes e depois
    assert uid.post("/login", data={"matricula": "2001", "senha": "senha1234"}).status_code == 302

    from app.db import get_db
    with app.app_context():
        usuario_id = get_db().execute("SELECT id FROM usuario WHERE matricula = '2001'").fetchone()["id"]
    resposta = admin.post(f"/admin/usuarios/{usuario_id}/senha", data={"senha": "novaSenha99"})

    assert resposta.status_code == 302
    cliente = app.test_client()
    assert cliente.post("/login", data={"matricula": "2001", "senha": "senha1234"}).status_code == 401
    assert cliente.post("/login", data={"matricula": "2001", "senha": "novaSenha99"}).status_code == 302


def test_redefinir_senha_fraca_e_recusada(admin, id_usuario, consulta):
    usuario_id = id_usuario("1001")
    antes = consulta("SELECT senha_hash FROM usuario WHERE id = ?", (usuario_id,))[0]["senha_hash"]

    admin.post(f"/admin/usuarios/{usuario_id}/senha", data={"senha": "123"})

    assert consulta("SELECT senha_hash FROM usuario WHERE id = ?", (usuario_id,))[0]["senha_hash"] == antes


def test_redefinir_senha_de_conta_inexistente_da_404(admin):
    assert admin.post("/admin/usuarios/99999/senha", data={"senha": "novaSenha99"}).status_code == 404


def test_colaborador_nao_acessa_nem_cria_contas(entrar, client, id_usuario, consulta):
    entrar("1001", "colab123")
    uid = id_usuario("1001")

    respostas = [client.get("/admin/usuarios/"), client.post("/admin/usuarios/", data=NOVA),
                 client.post(f"/admin/usuarios/{uid}/senha", data={"senha": "hackeada123"})]

    assert [r.status_code for r in respostas] == [403, 403, 403]
    assert consulta("SELECT COUNT(*) AS n FROM usuario")[0]["n"] == 3


def test_anonimo_vai_para_o_login(app):
    assert app.test_client().get("/admin/usuarios/").status_code == 302
