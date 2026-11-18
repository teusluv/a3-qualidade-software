"""RF-09 (mínimo): administração da situação dos cursos."""


def test_admin_altera_situacao_do_curso_e_gera_log(app, id_curso, consulta):
    admin = app.test_client()
    admin.post("/login", data={"matricula": "9001", "senha": "admin123"})

    resposta = admin.post(f"/admin/cursos/{id_curso('B')}/status", data={"status": "suspenso"})

    assert resposta.status_code == 302
    assert consulta("SELECT status FROM curso WHERE codigo = 'B'")[0]["status"] == "suspenso"
    assert "curso_status_alterado" in [r["acao"] for r in consulta("SELECT acao FROM log")]


def test_colaborador_nao_altera_situacao_do_curso(entrar, client, id_curso, consulta):
    entrar("1001", "colab123")

    resposta = client.post(f"/admin/cursos/{id_curso('B')}/status", data={"status": "arquivado"})

    assert resposta.status_code == 403
    assert consulta("SELECT status FROM curso WHERE codigo = 'B'")[0]["status"] == "ativo"


def test_situacao_invalida_e_rejeitada(app, id_curso, consulta):
    admin = app.test_client()
    admin.post("/login", data={"matricula": "9001", "senha": "admin123"})

    resposta = admin.post(f"/admin/cursos/{id_curso('B')}/status", data={"status": "apagado"})

    assert resposta.status_code == 400
    assert consulta("SELECT status FROM curso WHERE codigo = 'B'")[0]["status"] == "ativo"


def test_painel_admin_lista_cursos_e_eventos(app):
    admin = app.test_client()
    admin.post("/login", data={"matricula": "9001", "senha": "admin123"})

    pagina = admin.get("/admin/").get_data(as_text=True)

    assert "Segurança do Paciente" in pagina
    assert "login_sucesso" in pagina
