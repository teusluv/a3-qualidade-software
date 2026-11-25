"""Fixtures compartilhadas.

Isolamento: nenhum teste usa o banco do protótipo (instance/portal.db). Um banco modelo é
criado uma vez por sessão em pasta temporária; cada teste recebe uma CÓPIA nova dele.
"""

import shutil

import pytest

from app import create_app
from app.db import get_db, init_db
from app.seed_data import carregar_dados

CONFIG_TESTE = {
    "TESTING": True,
    "SECRET_KEY": "chave-somente-para-testes",
    "WTF_CSRF_ENABLED": False,  # os testes de CSRF ligam de novo explicitamente
}


@pytest.fixture(scope="session")
def banco_modelo(tmp_path_factory):
    caminho = tmp_path_factory.mktemp("modelo") / "modelo.db"
    app = create_app({**CONFIG_TESTE, "DATABASE": str(caminho)})
    with app.app_context():
        init_db()
        carregar_dados(get_db())
    return caminho


@pytest.fixture
def caminho_banco(tmp_path, banco_modelo):
    destino = tmp_path / "teste.db"
    shutil.copy(banco_modelo, destino)
    return destino


@pytest.fixture
def app(caminho_banco):
    pasta_uploads = str(caminho_banco.parent / "uploads")
    config = {**CONFIG_TESTE, "DATABASE": str(caminho_banco), "UPLOAD_FOLDER": pasta_uploads}
    return create_app(config)


@pytest.fixture
def app_com_csrf(caminho_banco):
    return create_app(
        {
            **CONFIG_TESTE,
            "DATABASE": str(caminho_banco),
            "UPLOAD_FOLDER": str(caminho_banco.parent / "uploads"),
            "WTF_CSRF_ENABLED": True,
        }
    )


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def entrar(client):
    """Faz login pelo formulário e devolve a resposta."""

    def _entrar(matricula, senha):
        return client.post("/login", data={"matricula": matricula, "senha": senha})

    return _entrar


@pytest.fixture
def consulta(app):
    """Executa um SELECT no banco de teste e devolve as linhas."""

    def _consulta(sql, parametros=()):
        with app.app_context():
            return get_db().execute(sql, parametros).fetchall()

    return _consulta


# ---------- apoio para os testes de fluxo ----------


@pytest.fixture
def executar(app):
    """Executa um comando de escrita no banco de teste (preparação de cenário)."""

    def _executar(sql, parametros=()):
        with app.app_context():
            db = get_db()
            cursor = db.execute(sql, parametros)
            db.commit()
            return cursor.lastrowid

    return _executar


@pytest.fixture
def id_curso(consulta):
    return lambda codigo: consulta("SELECT id FROM curso WHERE codigo = ?", (codigo,))[0]["id"]


@pytest.fixture
def id_usuario(consulta):
    return lambda matricula: consulta(
        "SELECT id FROM usuario WHERE matricula = ?", (matricula,)
    )[0]["id"]


@pytest.fixture
def concluir_todas(client, consulta):
    """Conclui todas as atividades de um curso pela interface."""

    def _concluir(curso_id):
        for linha in consulta("SELECT id FROM atividade WHERE curso_id = ?", (curso_id,)):
            client.post(f"/cursos/{curso_id}/atividades/{linha['id']}/concluir")

    return _concluir


@pytest.fixture
def responder(client, consulta):
    """Envia a avaliação acertando exatamente `acertos` questões. Devolve a resposta."""

    def _responder(curso_id, acertos):
        gabarito = consulta(
            "SELECT id, correta FROM questao WHERE curso_id = ? ORDER BY ordem", (curso_id,)
        )
        dados = {}
        for posicao, questao in enumerate(gabarito):
            if posicao < acertos:
                dados[f"q{questao['id']}"] = questao["correta"]
            else:
                dados[f"q{questao['id']}"] = "a" if questao["correta"] != "a" else "b"
        return client.post(f"/cursos/{curso_id}/avaliacao", data=dados)

    return _responder


@pytest.fixture
def aprovar_por_sql(app, id_curso, id_usuario):
    """Cria, direto no banco, um colaborador com curso concluído e aprovado.

    Insere inscrição, todas as atividades concluídas e uma tentativa com a nota informada.
    """

    def _aprovar(matricula, codigo_curso="A", nota=80, atividades_concluidas=None):
        uid, cid = id_usuario(matricula), id_curso(codigo_curso)
        with app.app_context():
            db = get_db()
            inscricao = db.execute(
                "INSERT INTO inscricao (usuario_id, curso_id, iniciado_em) VALUES (?, ?, ?)",
                (uid, cid, "2026-11-01T09:00:00"),
            ).lastrowid
            atividades = db.execute(
                "SELECT id FROM atividade WHERE curso_id = ? ORDER BY ordem", (cid,)
            ).fetchall()
            if atividades_concluidas is not None:
                atividades = atividades[:atividades_concluidas]
            for atividade in atividades:
                db.execute(
                    "INSERT INTO progresso (inscricao_id, atividade_id, concluida_em) "
                    "VALUES (?, ?, ?)",
                    (inscricao, atividade["id"], "2026-11-01T10:00:00"),
                )
            db.execute(
                "INSERT INTO tentativa (inscricao_id, acertos, total, nota, realizada_em) "
                "VALUES (?, ?, 10, ?, ?)",
                (inscricao, nota // 10, nota, "2026-11-02T11:00:00"),
            )
            db.commit()
        return inscricao

    return _aprovar
