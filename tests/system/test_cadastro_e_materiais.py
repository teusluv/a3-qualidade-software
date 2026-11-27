"""Administração: cadastro de curso e anexo de material (RF-09)."""

import io
from pathlib import Path

import pytest

PDF = b"%PDF-1.4\n1 0 obj\n<< >>\nendobj\ntrailer\n<< >>\n%%EOF\n"
CURSO_VALIDO = {
    "codigo": "e1", "titulo": "Biossegurança Básica", "carga_horaria": "6", "nota_minima": "75",
    "setor": "Enfermagem", "status": "ativo", "data_inicio": "2026-01-01",
    "data_fim": "2999-12-31", "obrigatorio": "on",
}


@pytest.fixture
def admin(app):
    cliente = app.test_client()
    cliente.post("/login", data={"matricula": "9001", "senha": "admin123"})
    return cliente


def _enviar(cliente, curso_id, conteudo=PDF, nome="aula.pdf"):
    return cliente.post(
        f"/admin/cursos/{curso_id}/materiais",
        data={"arquivo": (io.BytesIO(conteudo), nome)},
        content_type="multipart/form-data",
    )


# ---------- cadastro de curso ----------


def test_admin_cadastra_curso_com_atividades_e_questoes(admin, consulta):
    resposta = admin.post("/admin/cursos", data=CURSO_VALIDO)

    assert resposta.status_code == 302
    curso = consulta("SELECT * FROM curso WHERE codigo = 'E1'")[0]
    assert curso["nota_minima"] == 75
    assert curso["obrigatorio"] == 1
    sql = "SELECT COUNT(*) AS n FROM {} WHERE curso_id = ?"
    assert consulta(sql.format("atividade"), (curso["id"],))[0]["n"] == 4
    assert consulta(sql.format("questao"), (curso["id"],))[0]["n"] == 10
    assert "curso_criado" in [r["acao"] for r in consulta("SELECT acao FROM log")]


def test_curso_novo_aparece_para_o_colaborador_e_pode_ser_iniciado(admin, app, consulta):
    admin.post("/admin/cursos", data=CURSO_VALIDO)
    colaborador = app.test_client()
    colaborador.post("/login", data={"matricula": "1001", "senha": "colab123"})
    curso_id = consulta("SELECT id FROM curso WHERE codigo = 'E1'")[0]["id"]

    assert "Biossegurança Básica" in colaborador.get("/cursos").get_data(as_text=True)
    colaborador.post(f"/cursos/{curso_id}/iniciar")
    assert consulta("SELECT COUNT(*) AS n FROM inscricao")[0]["n"] == 1


@pytest.mark.parametrize(
    ("campo", "valor", "trecho"),
    [
        ("nota_minima", "60", "Nota mínima"),
        ("codigo", "A", "já existe"),  # o curso A já existe no seed
        ("titulo", "x", "Título"),
        ("data_fim", "2020-01-01", "anterior"),
    ],
)
def test_cadastro_invalido_mostra_erros_e_nao_grava(admin, consulta, campo, valor, trecho):
    antes = consulta("SELECT COUNT(*) AS n FROM curso")[0]["n"]

    resposta = admin.post("/admin/cursos", data={**CURSO_VALIDO, campo: valor})

    assert resposta.status_code == 400
    assert trecho in resposta.get_data(as_text=True)
    assert consulta("SELECT COUNT(*) AS n FROM curso")[0]["n"] == antes


def test_cadastro_invalido_mantem_o_que_foi_digitado(admin):
    resposta = admin.post("/admin/cursos", data={**CURSO_VALIDO, "nota_minima": "10"})

    assert "Biossegurança Básica" in resposta.get_data(as_text=True)


def test_colaborador_nao_cadastra_curso(entrar, client, consulta):
    entrar("1001", "colab123")

    resposta = client.post("/admin/cursos", data=CURSO_VALIDO)

    assert resposta.status_code == 403
    assert consulta("SELECT COUNT(*) AS n FROM curso WHERE codigo = 'E1'")[0]["n"] == 0


# ---------- material ----------


def test_admin_anexa_pdf_e_o_arquivo_fica_guardado(admin, app, id_curso, consulta):
    resposta = _enviar(admin, id_curso("A"))

    assert resposta.status_code == 302
    material = consulta("SELECT * FROM material")[0]
    assert material["nome_original"] == "aula.pdf"
    assert material["arquivo"] != "aula.pdf"  # o nome no disco é gerado
    assert (Path(app.config["UPLOAD_FOLDER"]) / material["arquivo"]).read_bytes() == PDF
    assert "material_enviado" in [r["acao"] for r in consulta("SELECT acao FROM log")]


@pytest.mark.parametrize(
    ("conteudo", "nome"),
    [
        (b"MZ\x90\x00 executavel", "programa.exe"),  # extensão proibida
        (b"MZ\x90\x00 executavel", "falso.pdf"),  # extensão ok, conteúdo não é PDF
        (b"<script>alert(1)</script>", "pagina.html"),
        (b"", "vazio.pdf"),
    ],
)
def test_arquivo_invalido_e_recusado(admin, id_curso, consulta, conteudo, nome):
    resposta = _enviar(admin, id_curso("A"), conteudo, nome)

    assert resposta.status_code == 302
    assert consulta("SELECT COUNT(*) AS n FROM material")[0]["n"] == 0


def test_envio_sem_escolher_arquivo_mostra_mensagem(admin, id_curso):
    resposta = admin.post(
        f"/admin/cursos/{id_curso('A')}/materiais", data={}, content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert "Escolha um arquivo" in resposta.get_data(as_text=True)


def test_nome_com_caminho_perigoso_nao_sai_da_pasta_de_uploads(admin, app, id_curso, consulta):
    _enviar(admin, id_curso("A"), PDF, "../../../etc/passwd.pdf")

    material = consulta("SELECT * FROM material")[0]
    assert "/" not in material["arquivo"]
    assert ".." not in material["nome_original"]
    assert (Path(app.config["UPLOAD_FOLDER"]) / material["arquivo"]).exists()


def test_arquivo_maior_que_o_limite_e_recusado_com_pagina_amigavel(app, id_curso):
    app.config["MAX_CONTENT_LENGTH"] = 1024
    admin = app.test_client()
    admin.post("/login", data={"matricula": "9001", "senha": "admin123"})

    resposta = _enviar(admin, id_curso("A"), PDF + b"x" * 5000)

    assert resposta.status_code == 413
    assert "muito grande" in resposta.get_data(as_text=True)


def test_colaborador_nao_anexa_material(entrar, client, id_curso, consulta):
    entrar("1001", "colab123")

    resposta = _enviar(client, id_curso("A"))

    assert resposta.status_code == 403
    assert consulta("SELECT COUNT(*) AS n FROM material")[0]["n"] == 0


def test_colaborador_baixa_o_material_so_depois_de_iniciar_o_curso(
    admin, app, id_curso, consulta
):
    curso = id_curso("A")
    _enviar(admin, curso)
    material_id = consulta("SELECT id FROM material")[0]["id"]
    colaborador = app.test_client()
    colaborador.post("/login", data={"matricula": "1001", "senha": "colab123"})
    url = f"/cursos/{curso}/materiais/{material_id}"

    antes = colaborador.get(url)
    colaborador.post(f"/cursos/{curso}/iniciar")
    depois = colaborador.get(url)

    assert antes.status_code == 403
    assert depois.status_code == 200
    assert depois.data == PDF
    assert "attachment" in depois.headers["Content-Disposition"]
    assert "aula.pdf" in depois.headers["Content-Disposition"]


def test_pagina_do_curso_lista_o_material_somente_depois_de_iniciar(
    admin, app, id_curso
):
    curso = id_curso("A")
    _enviar(admin, curso)
    colaborador = app.test_client()
    colaborador.post("/login", data={"matricula": "1001", "senha": "colab123"})

    antes = colaborador.get(f"/cursos/{curso}").get_data(as_text=True)
    colaborador.post(f"/cursos/{curso}/iniciar")
    depois = colaborador.get(f"/cursos/{curso}").get_data(as_text=True)

    assert "aula.pdf" not in antes
    assert "1 arquivo(s) de material" in antes
    assert "aula.pdf" in depois
    assert "Material do curso" in depois


def test_material_de_outro_curso_nao_e_acessivel_pela_url_do_curso_errado(
    admin, app, id_curso, consulta
):
    _enviar(admin, id_curso("A"))
    material_id = consulta("SELECT id FROM material")[0]["id"]
    colaborador = app.test_client()
    colaborador.post("/login", data={"matricula": "1001", "senha": "colab123"})
    curso_b = id_curso("B")
    colaborador.post(f"/cursos/{curso_b}/iniciar")

    resposta = colaborador.get(f"/cursos/{curso_b}/materiais/{material_id}")

    assert resposta.status_code == 404


def test_admin_remove_material_e_o_arquivo_some_do_disco(admin, app, id_curso, consulta):
    _enviar(admin, id_curso("A"))
    material = consulta("SELECT * FROM material")[0]
    caminho = Path(app.config["UPLOAD_FOLDER"]) / material["arquivo"]
    assert caminho.exists()

    resposta = admin.post(f"/admin/materiais/{material['id']}/remover")

    assert resposta.status_code == 302
    assert consulta("SELECT COUNT(*) AS n FROM material")[0]["n"] == 0
    assert not caminho.exists()
    assert "material_removido" in [r["acao"] for r in consulta("SELECT acao FROM log")]


def test_painel_admin_mostra_cadastro_e_a_pagina_do_curso_mostra_o_anexo(admin, id_curso):
    painel = admin.get("/admin/").get_data(as_text=True)
    pagina_do_curso = admin.get(f"/admin/cursos/{id_curso('A')}").get_data(as_text=True)

    assert "Cadastrar curso" in painel
    assert "Gerenciar" in painel
    assert "Anexar material" in pagina_do_curso
    assert 'enctype="multipart/form-data"' in pagina_do_curso
