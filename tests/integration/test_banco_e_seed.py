"""Isolamento do banco de teste e repetibilidade do seed."""

from pathlib import Path

from app.db import get_db
from app.seed_data import carregar_dados


def test_testes_nao_usam_o_banco_do_prototipo(app):
    banco_real = Path(app.instance_path) / "portal.db"

    assert Path(app.config["DATABASE"]) != banco_real
    assert "instance" not in Path(app.config["DATABASE"]).parts


def test_cada_teste_recebe_banco_novo_sem_alteracoes_de_outros_testes(entrar, consulta):
    # Se o banco fosse compartilhado, o log do teste de login anterior apareceria aqui.
    assert consulta("SELECT COUNT(*) AS n FROM log")[0]["n"] == 0
    entrar("1001", "colab123")
    assert consulta("SELECT COUNT(*) AS n FROM log")[0]["n"] == 1


def test_seed_cria_cenario_esperado(consulta):
    cursos = {linha["codigo"]: linha for linha in consulta("SELECT * FROM curso")}

    assert cursos["A"]["nota_minima"] == 70
    assert cursos["B"]["nota_minima"] == 80
    assert cursos["C"]["status"] == "suspenso"
    assert cursos["D"]["status"] == "arquivado"
    curso_a = (cursos["A"]["id"],)
    atividades = consulta("SELECT COUNT(*) AS n FROM atividade WHERE curso_id = ?", curso_a)
    questoes = consulta("SELECT COUNT(*) AS n FROM questao WHERE curso_id = ?", curso_a)
    assert atividades[0]["n"] == 4
    assert questoes[0]["n"] == 10


def test_seed_pode_rodar_de_novo_sem_duplicar(app):
    tabelas = ["usuario", "curso", "atividade", "questao"]

    def contagens():
        db = get_db()
        return {t: db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tabelas}  # noqa: S608

    with app.app_context():
        antes = contagens()
        carregar_dados(get_db())
        carregar_dados(get_db())
        assert contagens() == antes


def test_banco_vazio_recebe_as_tabelas_sem_quebrar(tmp_path):
    from app import create_app

    caminho = tmp_path / "vazio.db"
    app = create_app({"TESTING": True, "DATABASE": str(caminho), "SECRET_KEY": "t"})

    with app.app_context():
        total = get_db().execute("SELECT COUNT(*) FROM usuario").fetchone()[0]
    assert total == 0  # tabelas existem, mas sem dados: falta rodar o seed
    assert app.test_client().get("/login").status_code == 200


def test_banco_de_versao_anterior_e_recusado_com_mensagem_clara(tmp_path):
    import sqlite3

    import pytest

    from app import create_app

    caminho = tmp_path / "antigo.db"
    conexao = sqlite3.connect(caminho)
    conexao.execute("CREATE TABLE certificado (id INTEGER PRIMARY KEY, codigo TEXT)")
    conexao.commit()
    conexao.close()

    with pytest.raises(RuntimeError, match="Apague a pasta 'instance'"):
        create_app({"TESTING": True, "DATABASE": str(caminho), "SECRET_KEY": "t"})


def test_erro_inesperado_mostra_pagina_amigavel_sem_detalhes_internos(app):
    @app.get("/boom")
    def boom():
        raise RuntimeError("detalhe-interno-secreto")

    app.config["PROPAGATE_EXCEPTIONS"] = False
    resposta = app.test_client().get("/boom")

    assert resposta.status_code == 500
    pagina = resposta.get_data(as_text=True)
    assert "erro inesperado" in pagina
    assert "detalhe-interno-secreto" not in pagina
