"""Fluxo real com a proteção CSRF LIGADA (nos demais testes ela fica desligada)."""

import re


def _token(html: str) -> str:
    return re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html).group(1)


def test_login_iniciar_curso_e_logout_com_token(app_com_csrf, consulta):
    client = app_com_csrf.test_client()

    token = _token(client.get("/login").get_data(as_text=True))
    entrada = client.post(
        "/login", data={"matricula": "1001", "senha": "colab123", "csrf_token": token}
    )
    assert entrada.status_code == 302

    catalogo = client.get("/cursos").get_data(as_text=True)
    curso_a = consulta("SELECT id FROM curso WHERE codigo = 'A'")[0]["id"]
    pagina_curso = client.get(f"/cursos/{curso_a}").get_data(as_text=True)

    sem_token = client.post(f"/cursos/{curso_a}/iniciar")
    com_token = client.post(
        f"/cursos/{curso_a}/iniciar", data={"csrf_token": _token(pagina_curso)}
    )

    assert "Sair" in catalogo
    assert sem_token.status_code == 400  # sem token: rejeitado
    assert com_token.status_code == 302
    assert consulta("SELECT COUNT(*) AS n FROM inscricao")[0]["n"] == 1

    saida = client.post("/logout", data={"csrf_token": _token(catalogo)})
    assert saida.status_code == 302
