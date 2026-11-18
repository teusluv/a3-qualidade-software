"""CT-07 a CT-10, CT-13, CT-16: certificado (CA-07 a CA-10, CA-13, CA-16, A-07, A-04)."""

import io
import re
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor

from pypdf import PdfReader
from werkzeug.security import generate_password_hash

from app.db import get_db
from app.services import certificado


def _texto_do_pdf(conteudo: bytes) -> str:
    return " ".join(p.extract_text() for p in PdfReader(io.BytesIO(conteudo)).pages)


def _criar_usuarios(executar, quantidade, prefixo="9"):
    hash_qualquer = generate_password_hash("x")
    for numero in range(quantidade):
        executar(
            "INSERT INTO usuario (matricula, nome, senha_hash, perfil, setor) "
            "VALUES (?, ?, ?, 'colaborador', 'Farmácia')",
            (f"{prefixo}{numero:04d}", f"Colaborador Teste {numero}", hash_qualquer),
        )


# ---------- CT-07 / CA-07 ----------


def test_ct07_emitir_e_abrir_pdf_com_todos_os_campos(
    entrar, client, id_curso, concluir_todas, responder, consulta
):
    entrar("1001", "colab123")
    curso = id_curso("A")
    client.post(f"/cursos/{curso}/iniciar")
    concluir_todas(curso)
    responder(curso, 8)

    resposta = client.post(f"/cursos/{curso}/certificado", follow_redirects=True)
    texto = _texto_do_pdf(resposta.data)
    codigo = consulta("SELECT codigo FROM certificado")[0]["codigo"]

    assert resposta.status_code == 200
    assert resposta.mimetype == "application/pdf"
    for campo in ("Carla Mendes Lima", "1001", "Segurança do Paciente", "4 horas", codigo):
        assert campo in texto
    assert re.search(r"\d{2}/\d{2}/\d{4}", texto)  # data de conclusão


# ---------- CT-09 / CA-09 / RN-02 ----------


def test_ct09_reprovado_nao_emite_certificado(
    entrar, client, id_curso, concluir_todas, responder, consulta
):
    entrar("1001", "colab123")
    curso = id_curso("A")
    client.post(f"/cursos/{curso}/iniciar")
    concluir_todas(curso)
    responder(curso, 6)  # 60%: reprovado

    resposta = client.post(f"/cursos/{curso}/certificado", follow_redirects=True)

    assert resposta.mimetype != "application/pdf"
    assert "aprovado na avaliação" in resposta.get_data(as_text=True)
    assert consulta("SELECT COUNT(*) AS n FROM certificado")[0]["n"] == 0


def test_ct09_aprovado_com_atividades_incompletas_nao_emite(
    entrar, client, id_curso, aprovar_por_sql, consulta
):
    aprovar_por_sql("1001", "A", nota=90, atividades_concluidas=2)  # cenário forçado no banco
    entrar("1001", "colab123")

    resposta = client.post(f"/cursos/{id_curso('A')}/certificado", follow_redirects=True)

    assert resposta.mimetype != "application/pdf"
    assert "Conclua todas as atividades" in resposta.get_data(as_text=True)
    assert consulta("SELECT COUNT(*) AS n FROM certificado")[0]["n"] == 0


def test_ct09_sem_iniciar_o_curso_nao_emite(entrar, client, id_curso, consulta):
    entrar("1001", "colab123")

    resposta = client.post(f"/cursos/{id_curso('A')}/certificado", follow_redirects=True)

    assert resposta.mimetype != "application/pdf"
    assert consulta("SELECT COUNT(*) AS n FROM certificado")[0]["n"] == 0


def test_emissao_negada_fica_registrada_no_log(entrar, client, id_curso, consulta):
    entrar("1001", "colab123")
    client.post(f"/cursos/{id_curso('A')}/certificado")

    assert "emissao_negada" in [linha["acao"] for linha in consulta("SELECT acao FROM log")]


# ---------- A-07: emissão única ----------


def test_pedir_duas_vezes_devolve_o_mesmo_certificado(
    entrar, client, id_curso, aprovar_por_sql, consulta
):
    aprovar_por_sql("1001", "A")
    entrar("1001", "colab123")
    curso = id_curso("A")

    client.post(f"/cursos/{curso}/certificado")
    client.post(f"/cursos/{curso}/certificado")

    assert consulta("SELECT COUNT(*) AS n FROM certificado")[0]["n"] == 1
    emissoes = [r for r in consulta("SELECT acao FROM log") if r["acao"] == "certificado_emitido"]
    assert len(emissoes) == 1


def test_emissoes_simultaneas_geram_um_unico_certificado(
    app, caminho_banco, aprovar_por_sql, id_usuario, id_curso, consulta
):
    aprovar_por_sql("1001", "A")
    uid, cid = id_usuario("1001"), id_curso("A")

    def emitir_em_conexao_propria(_):
        conexao = sqlite3.connect(caminho_banco, timeout=30)
        conexao.row_factory = sqlite3.Row
        try:
            emitido, _criado = certificado.emitir_certificado(conexao, uid, cid)
            return emitido["codigo"]
        finally:
            conexao.close()

    with ThreadPoolExecutor(max_workers=8) as pool:
        codigos = list(pool.map(emitir_em_conexao_propria, range(8)))

    assert len(set(codigos)) == 1
    assert consulta("SELECT COUNT(*) AS n FROM certificado")[0]["n"] == 1


# ---------- CT-10 / CA-10 ----------


def test_ct10_cem_certificados_com_codigos_distintos(
    app, executar, aprovar_por_sql, id_usuario, id_curso
):
    _criar_usuarios(executar, 100)
    codigos = []
    for numero in range(100):
        matricula = f"9{numero:04d}"
        aprovar_por_sql(matricula, "A")
        with app.app_context():
            emitido, _ = certificado.emitir_certificado(
                get_db(), id_usuario(matricula), id_curso("A")
            )
            codigos.append(emitido["codigo"])

    assert len(codigos) == 100
    assert len(set(codigos)) == 100


# ---------- CT-08 / CA-08 (ambiente local, A-04) ----------


def test_ct08_vinte_emissoes_pelo_menos_19_em_ate_5_segundos(
    app, executar, aprovar_por_sql, id_usuario, id_curso
):
    _criar_usuarios(executar, 20)
    duracoes = []
    for numero in range(20):
        matricula = f"9{numero:04d}"
        aprovar_por_sql(matricula, "A")
        with app.app_context():
            inicio = time.perf_counter()
            emitido, _ = certificado.emitir_certificado(
                get_db(), id_usuario(matricula), id_curso("A")
            )
            certificado.gerar_pdf(certificado.obter_certificado_para_pdf(get_db(), emitido["id"]))
            duracoes.append(time.perf_counter() - inicio)

    assert sum(1 for d in duracoes if d <= 5) >= 19


# ---------- acesso ao PDF (RNF-06) ----------


def test_pdf_so_abre_para_o_dono_ou_para_o_administrador(
    app, entrar, client, id_curso, aprovar_por_sql, consulta
):
    aprovar_por_sql("1001", "A")
    entrar("1001", "colab123")
    client.post(f"/cursos/{id_curso('A')}/certificado")
    cert_id = consulta("SELECT id FROM certificado")[0]["id"]
    url = f"/certificados/{cert_id}/pdf"
    assert client.get(url).status_code == 200
    client.post("/logout")

    anonimo = app.test_client()
    outro = app.test_client()
    outro.post("/login", data={"matricula": "1002", "senha": "colab123"})
    admin = app.test_client()
    admin.post("/login", data={"matricula": "9001", "senha": "admin123"})

    assert anonimo.get(url).status_code == 302  # exige login
    assert outro.get(url).status_code == 404  # não é o dono
    assert admin.get(url).status_code == 200


# ---------- CT-16 / CA-16 ----------


def test_ct16_logs_de_login_avaliacao_e_emissao_com_usuario_e_data(
    entrar, client, id_curso, concluir_todas, responder, consulta, id_usuario
):
    entrar("1001", "colab123")
    curso = id_curso("A")
    client.post(f"/cursos/{curso}/iniciar")
    concluir_todas(curso)
    responder(curso, 8)
    client.post(f"/cursos/{curso}/certificado")

    logs = consulta("SELECT usuario_id, acao, criado_em FROM log")
    por_acao = {linha["acao"]: linha for linha in logs}

    for acao in ("login_sucesso", "avaliacao_realizada", "certificado_emitido"):
        assert por_acao[acao]["usuario_id"] == id_usuario("1001")
        assert por_acao[acao]["criado_em"]
    assert len([r for r in logs if r["acao"] == "certificado_emitido"]) == 1


def test_ct16_nenhuma_senha_em_texto_puro_no_banco(caminho_banco):
    conexao = sqlite3.connect(caminho_banco)
    try:
        tudo = " ".join(
            str(valor)
            for tabela in ("usuario", "log")
            for linha in conexao.execute(f"SELECT * FROM {tabela}")  # noqa: S608
            for valor in linha
        )
    finally:
        conexao.close()

    assert "colab123" not in tudo
    assert "admin123" not in tudo


# ---------- CT-13 / CA-13 / RN-05 ----------


def test_ct13_arquivar_curso_mantem_historico_e_certificado(
    app, entrar, client, id_curso, aprovar_por_sql, consulta
):
    aprovar_por_sql("1001", "A")
    entrar("1001", "colab123")
    curso = id_curso("A")
    client.post(f"/cursos/{curso}/certificado")
    cert_id = consulta("SELECT id FROM certificado")[0]["id"]

    admin = app.test_client()
    admin.post("/login", data={"matricula": "9001", "senha": "admin123"})
    admin.post(f"/admin/cursos/{curso}/status", data={"status": "arquivado"})

    catalogo = client.get("/cursos").get_data(as_text=True)
    historico = client.get("/historico").get_data(as_text=True)

    assert "Segurança do Paciente" not in catalogo  # não aparece como disponível
    assert "Segurança do Paciente" in historico  # histórico preservado
    assert f"/certificados/{cert_id}/pdf" in historico
    assert client.get(f"/certificados/{cert_id}/pdf").status_code == 200
