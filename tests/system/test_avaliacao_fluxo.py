"""CT-05 (sistema), CT-06: avaliação, nota, tentativas (CA-05, CA-06, A-02, A-06, A-07)."""

from app.db import get_db
from app.services import cursos


def _iniciar_e_concluir(client, id_curso, concluir_todas, codigo):
    curso = id_curso(codigo)
    client.post(f"/cursos/{curso}/iniciar")
    concluir_todas(curso)
    return curso


def _ultimo_resultado(resposta, client):
    return client.get(resposta.headers["Location"]).get_data(as_text=True)


def test_avaliacao_bloqueada_sem_atividades_concluidas(
    entrar, client, id_curso, consulta, responder
):
    entrar("1001", "colab123")
    curso = id_curso("A")
    client.post(f"/cursos/{curso}/iniciar")

    pelo_get = client.get(f"/cursos/{curso}/avaliacao")
    pelo_post = responder(curso, 10)  # tentativa de burlar enviando direto

    assert pelo_get.status_code == 302
    assert pelo_post.status_code == 302
    assert consulta("SELECT COUNT(*) AS n FROM tentativa")[0]["n"] == 0


def test_avaliacao_bloqueada_sem_iniciar_o_curso(entrar, id_curso, consulta, responder):
    entrar("1001", "colab123")

    resposta = responder(id_curso("A"), 10)

    assert resposta.status_code == 302
    assert consulta("SELECT COUNT(*) AS n FROM tentativa")[0]["n"] == 0


def test_formulario_nao_expoe_o_gabarito(
    app, entrar, client, id_curso, concluir_todas
):
    entrar("1001", "colab123")
    curso = _iniciar_e_concluir(client, id_curso, concluir_todas, "A")

    pagina = client.get(f"/cursos/{curso}/avaliacao").get_data(as_text=True)
    with app.app_context():
        colunas = cursos.listar_questoes(get_db(), curso)[0].keys()

    assert pagina.count('type="radio"') == 40  # 10 questões x 4 opções
    assert "checked" not in pagina  # nenhuma opção vem pré-marcada
    assert "correta" not in colunas  # a consulta das questões não traz o gabarito


def test_curso_a_sete_acertos_aprova_e_seis_reprova(
    entrar, client, id_curso, concluir_todas, responder
):
    entrar("1001", "colab123")
    curso = _iniciar_e_concluir(client, id_curso, concluir_todas, "A")

    sete = _ultimo_resultado(responder(curso, 7), client)
    seis = _ultimo_resultado(responder(curso, 6), client)

    assert "70%" in sete
    assert "Aprovado" in sete
    assert "60%" in seis
    assert "Reprovado" in seis


def test_curso_b_sete_acertos_reprova_e_oito_aprova(
    entrar, client, id_curso, concluir_todas, responder
):
    entrar("1001", "colab123")  # Enfermagem: vê o curso B
    curso = _iniciar_e_concluir(client, id_curso, concluir_todas, "B")

    sete = _ultimo_resultado(responder(curso, 7), client)
    oito = _ultimo_resultado(responder(curso, 8), client)

    assert "Reprovado" in sete
    assert "Aprovado" in oito


def test_ct06_quarta_tentativa_bloqueada_e_vale_a_maior_nota(
    entrar, client, id_curso, concluir_todas, responder, consulta
):
    entrar("1001", "colab123")
    curso = _iniciar_e_concluir(client, id_curso, concluir_todas, "A")

    for acertos in (6, 8, 7):  # notas 60%, 80% e 70%
        responder(curso, acertos)
    quarta = responder(curso, 10)
    pagina = client.get(quarta.headers["Location"]).get_data(as_text=True)

    assert "Limite de 3 tentativas atingido" in pagina
    assert consulta("SELECT COUNT(*) AS n FROM tentativa")[0]["n"] == 3
    assert "Melhor nota: <strong>80%</strong>" in pagina


def test_a07_tentativas_continuam_apos_aprovacao_ate_o_limite(
    entrar, client, id_curso, concluir_todas, responder, consulta
):
    entrar("1001", "colab123")
    curso = _iniciar_e_concluir(client, id_curso, concluir_todas, "A")

    responder(curso, 9)  # aprovado na 1ª
    segunda = responder(curso, 5)

    assert segunda.status_code == 302
    assert "/resultado/" in segunda.headers["Location"]
    assert consulta("SELECT COUNT(*) AS n FROM tentativa")[0]["n"] == 2


def test_questoes_sem_resposta_contam_como_erro(entrar, client, id_curso, concluir_todas):
    entrar("1001", "colab123")
    curso = _iniciar_e_concluir(client, id_curso, concluir_todas, "A")

    resposta = client.post(f"/cursos/{curso}/avaliacao", data={})
    pagina = client.get(resposta.headers["Location"]).get_data(as_text=True)

    assert "0%" in pagina
    assert "Reprovado" in pagina


def test_resposta_com_opcao_invalida_conta_como_erro(
    entrar, client, id_curso, concluir_todas, consulta
):
    entrar("1001", "colab123")
    curso = _iniciar_e_concluir(client, id_curso, concluir_todas, "A")
    questoes = consulta("SELECT id FROM questao WHERE curso_id = ?", (curso,))
    dados = {f"q{q['id']}": "z" for q in questoes}

    client.post(f"/cursos/{curso}/avaliacao", data=dados)

    assert consulta("SELECT nota FROM tentativa")[0]["nota"] == 0


def test_resultado_de_outro_usuario_nao_e_acessivel(
    app, entrar, client, id_curso, concluir_todas, responder
):
    entrar("1001", "colab123")
    curso = _iniciar_e_concluir(client, id_curso, concluir_todas, "A")
    resposta = responder(curso, 8)
    caminho = resposta.headers["Location"]
    client.post("/logout")

    outro = app.test_client()
    outro.post("/login", data={"matricula": "1002", "senha": "colab123"})

    assert outro.get(caminho).status_code == 404


def test_avaliacao_registra_log_com_usuario_e_data(
    entrar, client, id_curso, concluir_todas, responder, consulta, id_usuario
):
    entrar("1001", "colab123")
    curso = _iniciar_e_concluir(client, id_curso, concluir_todas, "A")
    responder(curso, 8)

    linha = consulta("SELECT usuario_id, criado_em FROM log WHERE acao = 'avaliacao_realizada'")[0]

    assert linha["usuario_id"] == id_usuario("1001")
    assert linha["criado_em"]
