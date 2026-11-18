"""Correções de segurança: cabeçalhos (D-03, D-04) e força bruta no login (D-02).

Casos levantados pela bateria OWASP de 18/11/2026 (docs/relatorio-seguranca.md).
"""

import pytest

from app.auth import MENSAGEM_LOGIN_BLOQUEADO, MENSAGEM_LOGIN_INVALIDO
from app.config import MAX_FALHAS_POR_MATRICULA, MAX_FALHAS_POR_ORIGEM

# ---------- D-03: cabeçalhos de segurança ----------

CABECALHOS_ESPERADOS = [
    "Content-Security-Policy",
    "X-Frame-Options",
    "X-Content-Type-Options",
    "Referrer-Policy",
    "Permissions-Policy",
]


@pytest.mark.parametrize("rota", ["/login", "/verificar", "/pagina-inexistente"])
@pytest.mark.parametrize("cabecalho", CABECALHOS_ESPERADOS)
def test_d03_cabecalhos_em_toda_resposta(client, rota, cabecalho):
    assert cabecalho in client.get(rota).headers


def test_d03_cabecalhos_tambem_em_pagina_protegida(entrar, client):
    entrar("1001", "colab123")

    resposta = client.get("/cursos")

    for cabecalho in CABECALHOS_ESPERADOS:
        assert cabecalho in resposta.headers


def test_d03_clickjacking_bloqueado(client):
    resposta = client.get("/login")

    assert resposta.headers["X-Frame-Options"] == "DENY"
    assert "frame-ancestors 'none'" in resposta.headers["Content-Security-Policy"]


def test_d03_csp_sem_script_embutido_e_com_o_cdn_do_bootstrap(client):
    csp = client.get("/login").headers["Content-Security-Policy"]

    assert "script-src 'self' https://cdn.jsdelivr.net" in csp
    assert "'unsafe-inline'" not in csp.split("script-src")[1].split(";")[0]


def test_d03_referrer_policy_protege_o_codigo_do_certificado(client):
    # O código vai na URL da verificação (D-01); no-referrer impede que vaze no Referer.
    assert client.get("/verificar").headers["Referrer-Policy"] == "no-referrer"


def test_d04_aplicacao_nao_tenta_mascarar_o_cabecalho_server(client):
    """D-04 é de implantação, não de código.

    Quem emite o cabeçalho Server é o servidor de desenvolvimento, antes da aplicação.
    Definir "Server" na resposta só duplicaria o cabeçalho, então a aplicação não o define;
    a correção é subir atrás de um servidor WSGI real com proxy.
    """
    assert "Server" not in client.get("/login").headers


def test_d03_hsts_so_em_https(client, caminho_banco):
    from app import create_app

    assert "Strict-Transport-Security" not in client.get("/login").headers

    app_https = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "chave-somente-para-testes",
            "WTF_CSRF_ENABLED": False,
            "DATABASE": str(caminho_banco),
            "SESSION_COOKIE_SECURE": True,
        }
    )
    resposta = app_https.test_client().get("/login")

    assert "Strict-Transport-Security" in resposta.headers


# ---------- D-02: força bruta no login ----------


def test_d02_bloqueia_apos_o_limite_de_falhas_na_mesma_matricula(entrar):
    for _ in range(MAX_FALHAS_POR_MATRICULA):
        assert entrar("1001", "senha-errada").status_code == 401

    bloqueada = entrar("1001", "outra-senha-errada")

    assert bloqueada.status_code == 429
    assert MENSAGEM_LOGIN_BLOQUEADO in bloqueada.get_data(as_text=True)


def test_d02_bloqueio_vale_mesmo_com_a_senha_certa(entrar, client):
    for _ in range(MAX_FALHAS_POR_MATRICULA):
        entrar("1001", "senha-errada")

    resposta = entrar("1001", "colab123")

    assert resposta.status_code == 429
    with client.session_transaction() as sessao:
        assert "usuario_id" not in sessao


def test_d02_mensagem_de_bloqueio_nao_revela_se_a_matricula_existe(entrar):
    for _ in range(MAX_FALHAS_POR_MATRICULA):
        entrar("1001", "x")
    existente = entrar("1001", "x").get_data(as_text=True)

    for _ in range(MAX_FALHAS_POR_MATRICULA):
        entrar("0000", "x")
    inexistente = entrar("0000", "x").get_data(as_text=True)

    assert MENSAGEM_LOGIN_BLOQUEADO in existente
    assert MENSAGEM_LOGIN_BLOQUEADO in inexistente


def test_d02_varredura_de_varias_matriculas_da_mesma_origem_e_contida(entrar):
    for numero in range(MAX_FALHAS_POR_ORIGEM):
        entrar(f"{2000 + numero}", "qualquer")

    bloqueada = entrar("9999", "qualquer")

    assert bloqueada.status_code == 429


def test_d02_login_certo_antes_do_limite_continua_funcionando(entrar, client):
    for _ in range(MAX_FALHAS_POR_MATRICULA - 1):
        assert entrar("1001", "senha-errada").status_code == 401

    resposta = entrar("1001", "colab123")

    assert resposta.status_code == 302
    with client.session_transaction() as sessao:
        assert "usuario_id" in sessao


def test_d02_login_certo_zera_o_contador(entrar, client):
    for _ in range(MAX_FALHAS_POR_MATRICULA - 1):
        entrar("1001", "senha-errada")
    entrar("1001", "colab123")
    client.post("/logout")

    for _ in range(MAX_FALHAS_POR_MATRICULA - 1):
        assert entrar("1001", "senha-errada").status_code == 401

    assert entrar("1001", "colab123").status_code == 302


def test_d02_bloqueio_fica_registrado_no_log(entrar, consulta):
    for _ in range(MAX_FALHAS_POR_MATRICULA + 1):
        entrar("1001", "senha-errada")

    eventos = consulta("SELECT acao FROM log WHERE acao = 'login_bloqueado'")

    assert len(eventos) >= 1


def test_d02_bloqueio_nao_guarda_o_que_foi_digitado(entrar, consulta):
    for _ in range(MAX_FALHAS_POR_MATRICULA + 1):
        entrar("1001", "senha-secreta-digitada")

    detalhes = [linha["detalhe"] or "" for linha in consulta("SELECT detalhe FROM log")]

    assert not any("senha-secreta-digitada" in detalhe for detalhe in detalhes)


def test_d02_outra_aplicacao_comeca_com_o_placar_limpo(entrar, caminho_banco):
    """O contador vive na aplicação: um servidor novo não herda bloqueio de outro."""
    from app import create_app

    for _ in range(MAX_FALHAS_POR_MATRICULA + 1):
        entrar("1001", "senha-errada")

    outra = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "chave-somente-para-testes",
            "WTF_CSRF_ENABLED": False,
            "DATABASE": str(caminho_banco),
        }
    )
    resposta = outra.test_client().post(
        "/login", data={"matricula": "1001", "senha": "colab123"}
    )

    assert resposta.status_code == 302


def test_d02_credenciais_invalidas_ainda_respondem_401_antes_do_limite(entrar):
    resposta = entrar("1001", "senha-errada")

    assert resposta.status_code == 401
    assert MENSAGEM_LOGIN_INVALIDO in resposta.get_data(as_text=True)
