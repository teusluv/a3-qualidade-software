"""CT-03 e CT-04: catálogo, início do curso e progresso (CA-03, CA-04, RN-04, A-08)."""


def test_catalogo_do_colaborador_de_enfermagem(entrar, client):
    entrar("1001", "colab123")

    pagina = client.get("/cursos").get_data(as_text=True)

    assert "Segurança do Paciente" in pagina
    assert "Higienização das Mãos" in pagina  # curso do setor Enfermagem
    assert "Biossegurança em Laboratório" in pagina  # suspenso aparece, mas indisponível
    assert "Protocolo Antigo de Triagem" not in pagina  # arquivado não aparece
    assert "Obrigatório" in pagina  # o curso A é obrigatório


def test_catalogo_nao_mostra_curso_de_outro_setor(entrar, client):
    entrar("1002", "colab123")  # Farmácia

    pagina = client.get("/cursos").get_data(as_text=True)

    assert "Segurança do Paciente" in pagina
    assert "Higienização das Mãos" not in pagina


def test_curso_de_outro_setor_nao_abre_pela_url(entrar, client, id_curso):
    entrar("1002", "colab123")

    assert client.get(f"/cursos/{id_curso('B')}").status_code == 404
    assert client.post(f"/cursos/{id_curso('B')}/iniciar").status_code == 404


def test_iniciar_curso_ativo(entrar, client, id_curso, consulta):
    entrar("1001", "colab123")

    client.post(f"/cursos/{id_curso('A')}/iniciar")

    assert consulta("SELECT COUNT(*) AS n FROM inscricao")[0]["n"] == 1


def test_iniciar_duas_vezes_nao_duplica_inscricao(entrar, client, id_curso, consulta):
    entrar("1001", "colab123")

    client.post(f"/cursos/{id_curso('A')}/iniciar")
    client.post(f"/cursos/{id_curso('A')}/iniciar")

    assert consulta("SELECT COUNT(*) AS n FROM inscricao")[0]["n"] == 1


def test_curso_suspenso_nao_pode_ser_iniciado(entrar, client, id_curso, consulta):
    entrar("1001", "colab123")

    resposta = client.post(f"/cursos/{id_curso('C')}/iniciar", follow_redirects=True)

    assert "não aceita novos inícios" in resposta.get_data(as_text=True)
    assert consulta("SELECT COUNT(*) AS n FROM inscricao")[0]["n"] == 0
    assert "inicio_bloqueado" in [r["acao"] for r in consulta("SELECT acao FROM log")]


def test_curso_fora_do_periodo_nao_pode_ser_iniciado(
    entrar, client, id_curso, executar, consulta
):
    executar("UPDATE curso SET data_fim = '2000-01-01' WHERE codigo = 'A'")
    entrar("1001", "colab123")

    client.post(f"/cursos/{id_curso('A')}/iniciar")

    assert consulta("SELECT COUNT(*) AS n FROM inscricao")[0]["n"] == 0


def test_curso_arquivado_nao_abre_sem_historico(entrar, client, id_curso):
    entrar("1001", "colab123")

    assert client.get(f"/cursos/{id_curso('D')}").status_code == 404
    assert client.post(f"/cursos/{id_curso('D')}/iniciar").status_code == 404


def test_quem_ja_iniciou_continua_apos_suspensao_ou_fim_do_periodo(
    entrar, client, id_curso, executar, consulta, concluir_todas, responder
):
    """A-08: só novos inícios são bloqueados."""
    entrar("1001", "colab123")
    curso = id_curso("A")
    client.post(f"/cursos/{curso}/iniciar")
    executar("UPDATE curso SET status = 'suspenso', data_fim = '2000-01-01' WHERE codigo = 'A'")

    concluir_todas(curso)
    resposta = responder(curso, 8)

    assert resposta.status_code == 302
    assert consulta("SELECT COUNT(*) AS n FROM tentativa")[0]["n"] == 1


def test_progresso_de_2_de_4_atividades_e_50_por_cento(
    entrar, client, id_curso, consulta
):
    entrar("1001", "colab123")
    curso = id_curso("A")
    client.post(f"/cursos/{curso}/iniciar")
    atividades = consulta("SELECT id FROM atividade WHERE curso_id = ? ORDER BY ordem", (curso,))

    for atividade in atividades[:2]:
        client.post(f"/cursos/{curso}/atividades/{atividade['id']}/concluir")
    pagina = client.get(f"/cursos/{curso}").get_data(as_text=True)

    assert "2 de 4 atividades concluídas" in pagina
    assert "50%" in pagina


def test_concluir_atividade_de_outro_curso_e_recusado(
    entrar, client, id_curso, consulta, executar
):
    entrar("1001", "colab123")
    curso_a, curso_b = id_curso("A"), id_curso("B")
    client.post(f"/cursos/{curso_a}/iniciar")
    atividade_de_b = consulta("SELECT id FROM atividade WHERE curso_id = ?", (curso_b,))[0]["id"]

    resposta = client.post(f"/cursos/{curso_a}/atividades/{atividade_de_b}/concluir")

    assert resposta.status_code == 404
    assert consulta("SELECT COUNT(*) AS n FROM progresso")[0]["n"] == 0


def test_nao_conclui_atividade_sem_iniciar_o_curso(entrar, client, id_curso, consulta):
    entrar("1001", "colab123")
    curso = id_curso("A")
    atividade = consulta("SELECT id FROM atividade WHERE curso_id = ?", (curso,))[0]["id"]

    client.post(f"/cursos/{curso}/atividades/{atividade}/concluir")

    assert consulta("SELECT COUNT(*) AS n FROM progresso")[0]["n"] == 0
