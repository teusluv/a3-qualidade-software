"""RNF-07: proteção da sessão e dos formulários."""

from datetime import timedelta


def test_cookie_de_sessao_tem_httponly_e_samesite(entrar):
    resposta = entrar("1001", "colab123")

    cookie = resposta.headers["Set-Cookie"]

    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie


def test_sessao_expira_em_no_maximo_30_minutos(app):
    assert app.config["PERMANENT_SESSION_LIFETIME"] <= timedelta(minutes=30)


def test_login_sem_token_csrf_e_rejeitado(app_com_csrf):
    client = app_com_csrf.test_client()

    resposta = client.post("/login", data={"matricula": "1001", "senha": "colab123"})

    assert resposta.status_code == 400
    with client.session_transaction() as sessao:
        assert "usuario_id" not in sessao
