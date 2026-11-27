"""Gestão do curso pelo administrador: dados, código, exclusão, atividades, questões, links."""

import io
from pathlib import Path

import pytest

PDF = b"%PDF-1.4\n1 0 obj\n<< >>\nendobj\ntrailer\n<< >>\n%%EOF\n"
NOVO = {
    "codigo": "e1", "titulo": "Biossegurança Básica", "carga_horaria": "6", "nota_minima": "75",
    "setor": "", "status": "ativo", "data_inicio": "2026-01-01", "data_fim": "2999-12-31",
}
QUESTAO = {
    "enunciado": "Qual é a resposta nova?", "opcao_a": "Alfa", "opcao_b": "Beta",
    "opcao_c": "Gama", "opcao_d": "Delta", "correta": "d",
}


@pytest.fixture
def admin(app):
    cliente = app.test_client()
    cliente.post("/login", data={"matricula": "9001", "senha": "admin123"})
    return cliente


@pytest.fixture
def curso_novo(admin, id_curso):
    """Cria o curso E1 (sem nenhum histórico) e devolve o id."""
    admin.post("/admin/cursos", data=NOVO)
    return id_curso("E1")


def _sql(consulta, sql, p=()):
    return consulta(sql, p)


# ---------- acesso ----------


def test_pagina_do_curso_so_para_administrador(entrar, client, app, id_curso):
    url = f"/admin/cursos/{id_curso('A')}"

    anonimo = app.test_client().get(url)
    entrar("1001", "colab123")
    colaborador = client.get(url)

    assert anonimo.status_code == 302
    assert colaborador.status_code == 403


def test_pagina_do_curso_inexistente_da_404(admin):
    assert admin.get("/admin/cursos/99999").status_code == 404


def test_pagina_do_curso_mostra_todas_as_secoes(admin, id_curso):
    pagina = admin.get(f"/admin/cursos/{id_curso('A')}").get_data(as_text=True)

    for secao in ("Dados do curso", "Atividades", "Perguntas e respostas", "Vídeos e links",
                  "Material (arquivos)", "Quem concluiu este curso", "Excluir curso"):
        assert secao in pagina


# ---------- código do curso ----------


def test_formulario_de_cadastro_explica_as_regras_e_lista_os_codigos_usados(admin):
    pagina = admin.get("/admin/").get_data(as_text=True)

    assert "letras sem acento (A a Z) e números (0 a 9)" in pagina
    assert "não pode repetir" in pagina
    assert "Códigos já usados:" in pagina
    for codigo in ("A", "B", "C", "D"):
        assert f"<strong>{codigo}" in pagina or codigo in pagina.split("Códigos já usados:")[1][:80]
    assert 'pattern="[A-Za-z0-9]{1,10}"' in pagina


@pytest.mark.parametrize("codigo", ["A", "a"])
def test_codigo_repetido_e_recusado_mesmo_em_minuscula(admin, consulta, codigo):
    antes = consulta("SELECT COUNT(*) AS n FROM curso")[0]["n"]

    resposta = admin.post("/admin/cursos", data={**NOVO, "codigo": codigo})

    assert resposta.status_code == 400
    assert "já existe um curso com este código" in resposta.get_data(as_text=True)
    assert consulta("SELECT COUNT(*) AS n FROM curso")[0]["n"] == antes


# ---------- editar dados ----------


def test_editar_dados_do_curso(admin, id_curso, consulta):
    curso = id_curso("B")

    resposta = admin.post(f"/admin/cursos/{curso}/editar", data={
        **NOVO, "codigo": "b", "titulo": "Higiene das Mãos (revisado)", "nota_minima": "85",
        "setor": "Enfermagem", "status": "ativo", "obrigatorio": "on"})

    assert resposta.status_code == 302
    linha = consulta("SELECT * FROM curso WHERE id = ?", (curso,))[0]
    assert (linha["titulo"], linha["nota_minima"], linha["obrigatorio"]) == (
        "Higiene das Mãos (revisado)", 85, 1)
    assert "curso_editado" in [r["acao"] for r in consulta("SELECT acao FROM log")]


def test_editar_mantendo_o_proprio_codigo_nao_conta_como_repetido(admin, id_curso):
    curso = id_curso("A")

    resposta = admin.post(f"/admin/cursos/{curso}/editar", data={**NOVO, "codigo": "A"})

    assert resposta.status_code == 302


def test_editar_para_codigo_de_outro_curso_e_recusado(admin, id_curso, consulta):
    resposta = admin.post(f"/admin/cursos/{id_curso('B')}/editar", data={**NOVO, "codigo": "A"})

    assert resposta.status_code == 400
    assert "já existe outro curso" in resposta.get_data(as_text=True)
    assert consulta("SELECT codigo FROM curso WHERE id = ?", (id_curso("B"),))[0]["codigo"] == "B"


def test_editar_com_nota_abaixo_de_70_e_recusado_e_mantem_o_digitado(admin, id_curso, consulta):
    curso = id_curso("A")

    resposta = admin.post(f"/admin/cursos/{curso}/editar",
                          data={**NOVO, "codigo": "A", "titulo": "Titulo Digitado", "nota_minima": "50"})

    assert resposta.status_code == 400
    assert "Titulo Digitado" in resposta.get_data(as_text=True)
    assert consulta("SELECT nota_minima FROM curso WHERE id = ?", (curso,))[0]["nota_minima"] == 70


def test_editar_para_arquivado(admin, id_curso, consulta):
    curso = id_curso("A")

    admin.post(f"/admin/cursos/{curso}/editar", data={**NOVO, "codigo": "A", "status": "arquivado"})

    assert consulta("SELECT status FROM curso WHERE id = ?", (curso,))[0]["status"] == "arquivado"


def test_colaborador_nao_edita_nem_exclui(entrar, client, id_curso, consulta):
    entrar("1001", "colab123")
    curso = id_curso("A")

    editar = client.post(f"/admin/cursos/{curso}/editar", data={**NOVO, "codigo": "A", "titulo": "Hackeado"})
    excluir = client.post(f"/admin/cursos/{curso}/excluir", data={"confirmacao": "A"})

    assert (editar.status_code, excluir.status_code) == (403, 403)
    assert consulta("SELECT titulo FROM curso WHERE id = ?", (curso,))[0]["titulo"] != "Hackeado"


# ---------- excluir ----------


def test_excluir_curso_sem_historico_apaga_tudo_o_que_e_dele(admin, app, curso_novo, consulta):
    admin.post(f"/admin/cursos/{curso_novo}/materiais",
               data={"arquivo": (io.BytesIO(PDF), "aula.pdf")}, content_type="multipart/form-data")
    admin.post(f"/admin/cursos/{curso_novo}/links", data={"titulo": "Aula", "url": "https://exemplo.com"})
    arquivo = Path(app.config["UPLOAD_FOLDER"]) / consulta("SELECT arquivo FROM material")[0]["arquivo"]
    assert arquivo.exists()

    resposta = admin.post(f"/admin/cursos/{curso_novo}/excluir", data={"confirmacao": "e1"})

    assert resposta.status_code == 302
    for tabela in ("curso", "atividade", "questao", "material", "link_curso"):
        coluna = "id" if tabela == "curso" else "curso_id"
        assert consulta(f"SELECT COUNT(*) AS n FROM {tabela} WHERE {coluna} = ?", (curso_novo,))[0]["n"] == 0  # noqa: S608
    assert not arquivo.exists()
    assert "curso_excluido" in [r["acao"] for r in consulta("SELECT acao FROM log")]


def test_excluir_exige_digitar_o_codigo(admin, curso_novo, consulta):
    for confirmacao in ("", "errado", "A"):
        admin.post(f"/admin/cursos/{curso_novo}/excluir", data={"confirmacao": confirmacao})

    assert consulta("SELECT COUNT(*) AS n FROM curso WHERE id = ?", (curso_novo,))[0]["n"] == 1


def test_curso_com_historico_nao_pode_ser_excluido(admin, id_curso, aprovar_por_sql, consulta):
    aprovar_por_sql("1001", "A")
    curso = id_curso("A")

    pagina = admin.get(f"/admin/cursos/{curso}").get_data(as_text=True)
    resposta = admin.post(f"/admin/cursos/{curso}/excluir", data={"confirmacao": "A"}, follow_redirects=True)

    assert "não pode ser excluído" in pagina
    assert "Excluir curso</button>" not in pagina  # nem aparece o botão
    assert "não pode ser excluído" in resposta.get_data(as_text=True)
    assert consulta("SELECT COUNT(*) AS n FROM curso WHERE id = ?", (curso,))[0]["n"] == 1


# ---------- atividades ----------


def test_adicionar_renomear_e_remover_atividade(admin, curso_novo, consulta):
    admin.post(f"/admin/cursos/{curso_novo}/atividades", data={"titulo": "Quinta atividade"})
    ativ = consulta("SELECT * FROM atividade WHERE curso_id = ? ORDER BY ordem", (curso_novo,))
    assert [a["titulo"] for a in ativ][-1] == "Quinta atividade"
    assert ativ[-1]["ordem"] == 5

    admin.post(f"/admin/atividades/{ativ[-1]['id']}/editar", data={"titulo": "Quinta renomeada"})
    assert consulta("SELECT titulo FROM atividade WHERE id = ?", (ativ[-1]["id"],))[0]["titulo"] == "Quinta renomeada"

    admin.post(f"/admin/atividades/{ativ[-1]['id']}/remover")
    assert consulta("SELECT COUNT(*) AS n FROM atividade WHERE curso_id = ?", (curso_novo,))[0]["n"] == 4


def test_atividade_com_titulo_invalido_e_recusada(admin, curso_novo, consulta):
    admin.post(f"/admin/cursos/{curso_novo}/atividades", data={"titulo": "ab"})

    assert consulta("SELECT COUNT(*) AS n FROM atividade WHERE curso_id = ?", (curso_novo,))[0]["n"] == 4


def test_atividade_ja_concluida_por_alguem_nao_pode_ser_removida(admin, id_curso, aprovar_por_sql, consulta):
    aprovar_por_sql("1001", "A")
    atividade = consulta("SELECT id FROM atividade WHERE curso_id = ? ORDER BY ordem", (id_curso("A"),))[0]["id"]

    resposta = admin.post(f"/admin/atividades/{atividade}/remover", follow_redirects=True)

    assert "não pode ser removida" in resposta.get_data(as_text=True)
    assert consulta("SELECT COUNT(*) AS n FROM atividade WHERE id = ?", (atividade,))[0]["n"] == 1


def test_adicionar_atividade_exige_que_quem_ja_concluiu_conclua_a_nova(
    admin, app, id_curso, aprovar_por_sql
):
    curso = id_curso("A")
    aprovar_por_sql("1001", "A", nota=80)
    colaborador = app.test_client()
    colaborador.post("/login", data={"matricula": "1001", "senha": "colab123"})
    assert colaborador.get(f"/cursos/{curso}/avaliacao").status_code == 200  # liberada

    admin.post(f"/admin/cursos/{curso}/atividades", data={"titulo": "Atividade nova obrigatória"})

    assert colaborador.get(f"/cursos/{curso}/avaliacao").status_code == 302  # bloqueada de novo


# ---------- perguntas e respostas ----------


def test_admin_ve_as_perguntas_e_as_respostas_certas(admin, id_curso, consulta):
    curso = id_curso("A")
    q = consulta("SELECT * FROM questao WHERE curso_id = ? ORDER BY ordem", (curso,))[0]

    pagina = admin.get(f"/admin/cursos/{curso}").get_data(as_text=True)

    assert q["enunciado"] in pagina
    assert f"certa: {q['correta'].upper()}" in pagina
    assert "10 pergunta(s) cadastrada(s)" in pagina


def test_adicionar_pergunta_aparece_na_avaliacao(admin, app, id_curso, concluir_todas, consulta):
    curso = id_curso("A")

    admin.post(f"/admin/cursos/{curso}/questoes", data=QUESTAO)

    assert consulta("SELECT COUNT(*) AS n FROM questao WHERE curso_id = ?", (curso,))[0]["n"] == 11
    colaborador = app.test_client()
    colaborador.post("/login", data={"matricula": "1001", "senha": "colab123"})
    colaborador.post(f"/cursos/{curso}/iniciar")
    for a in consulta("SELECT id FROM atividade WHERE curso_id = ?", (curso,)):
        colaborador.post(f"/cursos/{curso}/atividades/{a['id']}/concluir")
    pagina = colaborador.get(f"/cursos/{curso}/avaliacao").get_data(as_text=True)
    assert "Qual é a resposta nova?" in pagina
    assert pagina.count('type="radio"') == 44  # 11 perguntas x 4 respostas


def test_editar_a_resposta_certa_muda_a_correcao_das_proximas_tentativas(
    admin, app, id_curso, consulta
):
    curso = id_curso("A")
    q = consulta("SELECT * FROM questao WHERE curso_id = ? ORDER BY ordem", (curso,))[0]
    nova_certa = "a" if q["correta"] != "a" else "b"

    admin.post(f"/admin/questoes/{q['id']}/editar", data={
        "enunciado": q["enunciado"], "opcao_a": q["opcao_a"], "opcao_b": q["opcao_b"],
        "opcao_c": q["opcao_c"], "opcao_d": q["opcao_d"], "correta": nova_certa})

    assert consulta("SELECT correta FROM questao WHERE id = ?", (q["id"],))[0]["correta"] == nova_certa
    assert "questao_editada" in [r["acao"] for r in consulta("SELECT acao FROM log")]


def test_pergunta_invalida_nao_e_gravada(admin, id_curso, consulta):
    curso = id_curso("A")

    admin.post(f"/admin/cursos/{curso}/questoes", data={**QUESTAO, "opcao_b": "Alfa"})  # repetida
    admin.post(f"/admin/cursos/{curso}/questoes", data={**QUESTAO, "correta": "z"})
    admin.post(f"/admin/cursos/{curso}/questoes", data={**QUESTAO, "enunciado": "abc"})

    assert consulta("SELECT COUNT(*) AS n FROM questao WHERE curso_id = ?", (curso,))[0]["n"] == 10


def test_remover_pergunta(admin, id_curso, consulta):
    curso = id_curso("A")
    q = consulta("SELECT id FROM questao WHERE curso_id = ? ORDER BY ordem", (curso,))[0]["id"]

    admin.post(f"/admin/questoes/{q}/remover")

    assert consulta("SELECT COUNT(*) AS n FROM questao WHERE curso_id = ?", (curso,))[0]["n"] == 9


def test_colaborador_nao_mexe_nas_perguntas(entrar, client, id_curso, consulta):
    entrar("1001", "colab123")
    curso = id_curso("A")
    q = consulta("SELECT id FROM questao WHERE curso_id = ?", (curso,))[0]["id"]

    respostas = [client.post(f"/admin/cursos/{curso}/questoes", data=QUESTAO),
                 client.post(f"/admin/questoes/{q}/editar", data=QUESTAO),
                 client.post(f"/admin/questoes/{q}/remover")]

    assert [r.status_code for r in respostas] == [403, 403, 403]


# ---------- links de vídeo ----------


def test_link_aparece_para_o_colaborador_so_depois_de_iniciar_e_abre_em_nova_aba(
    admin, app, id_curso
):
    curso = id_curso("A")
    admin.post(f"/admin/cursos/{curso}/links",
               data={"titulo": "Vídeo de boas-vindas", "url": "https://www.youtube.com/watch?v=abc"})
    colaborador = app.test_client()
    colaborador.post("/login", data={"matricula": "1001", "senha": "colab123"})

    antes = colaborador.get(f"/cursos/{curso}").get_data(as_text=True)
    colaborador.post(f"/cursos/{curso}/iniciar")
    depois = colaborador.get(f"/cursos/{curso}").get_data(as_text=True)

    assert "youtube.com" not in antes
    assert "1 link(s) de vídeo" in antes
    assert 'href="https://www.youtube.com/watch?v=abc"' in depois
    assert 'target="_blank" rel="noopener noreferrer"' in depois
    assert "Vídeo de boas-vindas" in depois


@pytest.mark.parametrize("url", ["javascript:alert(1)", "data:text/html,x", "ftp://x/y", "youtube.com/abc"])
def test_link_inseguro_nao_e_gravado(admin, id_curso, consulta, url):
    admin.post(f"/admin/cursos/{id_curso('A')}/links", data={"titulo": "Vídeo", "url": url})

    assert consulta("SELECT COUNT(*) AS n FROM link_curso")[0]["n"] == 0


def test_remover_link(admin, id_curso, consulta):
    curso = id_curso("A")
    admin.post(f"/admin/cursos/{curso}/links", data={"titulo": "Vídeo", "url": "https://exemplo.com"})
    link = consulta("SELECT id FROM link_curso")[0]["id"]

    admin.post(f"/admin/links/{link}/remover")

    assert consulta("SELECT COUNT(*) AS n FROM link_curso")[0]["n"] == 0


# ---------- concluintes ----------


def test_admin_ve_quem_concluiu_o_curso_mesmo_arquivado(admin, app, id_curso, aprovar_por_sql, consulta):
    aprovar_por_sql("1001", "A", nota=90)
    colaborador = app.test_client()
    colaborador.post("/login", data={"matricula": "1001", "senha": "colab123"})
    curso = id_curso("A")
    colaborador.post(f"/cursos/{curso}/certificado")
    codigo = consulta("SELECT codigo FROM certificado")[0]["codigo"]
    admin.post(f"/admin/cursos/{curso}/status", data={"status": "arquivado"})

    pagina = admin.get(f"/admin/cursos/{curso}").get_data(as_text=True)

    assert "Carla Mendes Lima" in pagina
    assert "1001" in pagina
    assert codigo in pagina
    assert "90%" in pagina


# ---------- material: volta para a página do curso ----------


def test_anexar_e_remover_material_voltam_para_a_pagina_do_curso(admin, id_curso, consulta):
    curso = id_curso("A")

    envio = admin.post(f"/admin/cursos/{curso}/materiais",
                       data={"arquivo": (io.BytesIO(PDF), "aula.pdf")}, content_type="multipart/form-data")
    material = consulta("SELECT id FROM material")[0]["id"]
    remocao = admin.post(f"/admin/materiais/{material}/remover")

    assert envio.headers["Location"].endswith(f"/admin/cursos/{curso}#material")
    assert remocao.headers["Location"].endswith(f"/admin/cursos/{curso}#material")
