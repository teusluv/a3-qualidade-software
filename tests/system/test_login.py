"""CT-01: login (CA-01, CA-16). Caixa-preta, pelo formulário."""

import pytest
from werkzeug.security import check_password_hash

from app.auth import MENSAGEM_LOGIN_INVALIDO


def test_login_valido_redireciona_para_o_catalogo(entrar, client):
    resposta = entrar("1001", "colab123")

    assert resposta.status_code == 302
    assert resposta.headers["Location"] == "/cursos"
    with client.session_transaction() as sessao:
        assert "usuario_id" in sessao


def test_login_valido_mostra_nome_do_usuario(entrar, client):
    entrar("1001", "colab123")

    pagina = client.get("/cursos")

    assert pagina.status_code == 200
    assert "Carla Mendes Lima" in pagina.get_data(as_text=True)


@pytest.mark.parametrize(
    ("matricula", "senha"),
    [
        ("1001", "senha-errada"),  # matrícula certa, senha errada
        ("0000", "colab123"),  # matrícula inexistente
        ("", ""),  # campos vazios
        ("1001", ""),  # senha vazia
        ("", "colab123"),  # matrícula vazia
        ("x" * 500, "colab123"),  # entrada fora do tamanho
    ],
)
def test_credenciais_invalidas_negam_acesso_com_mensagem_generica(entrar, client, matricula, senha):
    resposta = entrar(matricula, senha)

    assert resposta.status_code == 401
    assert MENSAGEM_LOGIN_INVALIDO in resposta.get_data(as_text=True)
    with client.session_transaction() as sessao:
        assert "usuario_id" not in sessao


def test_mensagem_nao_revela_qual_campo_esta_errado(entrar):
    senha_errada = entrar("1001", "senha-errada").get_data(as_text=True)
    matricula_errada = entrar("0000", "colab123").get_data(as_text=True)

    assert MENSAGEM_LOGIN_INVALIDO in senha_errada
    assert MENSAGEM_LOGIN_INVALIDO in matricula_errada


def test_entrada_com_sql_injection_nao_autentica(entrar, consulta):
    resposta = entrar("' OR '1'='1", "' OR '1'='1")

    assert resposta.status_code == 401
    assert consulta("SELECT COUNT(*) AS n FROM usuario")[0]["n"] == 3  # tabela intacta


def test_senha_fica_armazenada_com_hash(consulta):
    linha = consulta("SELECT senha_hash FROM usuario WHERE matricula = '1001'")[0]

    assert linha["senha_hash"] != "colab123"
    assert check_password_hash(linha["senha_hash"], "colab123")


def test_logs_registram_sucesso_e_falha_sem_guardar_senha(entrar, consulta):
    entrar("1001", "senha-errada")
    entrar("1001", "colab123")

    logs = consulta("SELECT usuario_id, acao, detalhe FROM log ORDER BY id")

    assert [linha["acao"] for linha in logs] == ["login_falha", "login_sucesso"]
    for linha in logs:
        assert linha["usuario_id"] is not None
        assert "senha" not in str(linha["detalhe"]).lower()
        assert "colab123" not in str(tuple(linha))


def test_falha_de_login_nao_grava_o_que_foi_digitado(entrar, consulta):
    entrar("matricula-inexistente", "senha-qualquer")

    linha = consulta("SELECT usuario_id, detalhe FROM log")[0]

    assert linha["usuario_id"] is None
    assert linha["detalhe"] is None


def test_logout_encerra_a_sessao(entrar, client):
    entrar("1001", "colab123")

    resposta = client.post("/logout")

    assert resposta.status_code == 302
    with client.session_transaction() as sessao:
        assert "usuario_id" not in sessao
    assert client.get("/").status_code == 302  # volta a exigir login
