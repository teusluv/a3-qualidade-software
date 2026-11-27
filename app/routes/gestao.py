"""Gestão de cursos pelo administrador: dados, atividades, questões, links, concluintes,
exclusão, eventos e visualização do banco (RF-09, CA-16)."""

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)

from app.auth import perfil_required
from app.config import EXTENSOES_PERMITIDAS, NOTA_MINIMA_PADRAO
from app.db import get_db
from app.services import banco, cadastro, conteudo, cursos, logs, materiais
from app.services.logs import registrar

bp = Blueprint("gestao", __name__, url_prefix="/admin")

STATUS_EDICAO = ("ativo", "suspenso", "arquivado")


def _setores(db) -> list[str]:
    linhas = db.execute("SELECT DISTINCT setor FROM usuario ORDER BY setor").fetchall()
    return [linha["setor"] for linha in linhas]


def _curso_ou_404(db, curso_id: int):
    curso = db.execute("SELECT * FROM curso WHERE id = ?", (curso_id,)).fetchone()
    if curso is None:
        abort(404)
    return curso


def _volta(curso_id: int, ancora: str = ""):
    return redirect(url_for("gestao.curso", curso_id=curso_id) + ancora)


def _avisar_erros(erros: list[str]) -> None:
    for erro in erros:
        flash(erro, "warning")


def _pagina_do_curso(db, curso, valores=None, erros=None):
    codigos_dos_outros = [c for c in cadastro.listar_codigos(db) if c != curso["codigo"]]
    return render_template(
        "admin_curso.html",
        curso=curso,
        valores=valores or {},
        erros=erros or [],
        setores=_setores(db),
        status_edicao=STATUS_EDICAO,
        codigos_dos_outros=codigos_dos_outros,
        nota_minima_padrao=NOTA_MINIMA_PADRAO,
        atividades=conteudo.listar_atividades_admin(db, curso["id"]),
        questoes=conteudo.listar_questoes_admin(db, curso["id"]),
        links=conteudo.listar_links(db, curso["id"]),
        materiais=materiais.listar_materiais(db, curso["id"]),
        concluintes=cursos.listar_concluintes(db, curso["id"]),
        tem_historico=cadastro.curso_tem_historico(db, curso["id"]),
        extensoes=", ".join(EXTENSOES_PERMITIDAS),
    )


# ---------- página do curso e dados ----------


@bp.get("/cursos/<int:curso_id>")
@perfil_required("administrador")
def curso(curso_id: int):
    db = get_db()
    return _pagina_do_curso(db, _curso_ou_404(db, curso_id))


@bp.post("/cursos/<int:curso_id>/editar")
@perfil_required("administrador")
def editar_curso(curso_id: int):
    db = get_db()
    atual = _curso_ou_404(db, curso_id)
    dados, erros = cadastro.validar_curso(request.form, set(_setores(db)), STATUS_EDICAO)
    if not erros and cadastro.codigo_existe(db, dados["codigo"], ignorar_id=curso_id):
        erros.append("Código: já existe outro curso com este código.")
    if erros:
        return _pagina_do_curso(db, atual, request.form, erros), 400

    cadastro.atualizar_curso(db, curso_id, dados)
    registrar(db, "curso_editado", g.usuario["id"], f"curso={dados['codigo']}")
    db.commit()
    flash("Dados do curso salvos.", "success")
    return _volta(curso_id)


@bp.post("/cursos/<int:curso_id>/excluir")
@perfil_required("administrador")
def excluir_curso(curso_id: int):
    db = get_db()
    curso = _curso_ou_404(db, curso_id)
    if request.form.get("confirmacao", "").strip().upper() != curso["codigo"]:
        flash(f"Para excluir, digite o código {curso['codigo']} para confirmar.", "warning")
        return _volta(curso_id, "#excluir")
    try:
        cadastro.excluir_curso(db, current_app.config["UPLOAD_FOLDER"], curso_id)
    except cadastro.CursoComHistoricoError as erro:
        flash(str(erro), "warning")
        return _volta(curso_id, "#excluir")
    registrar(db, "curso_excluido", g.usuario["id"], f"curso={curso['codigo']}")
    db.commit()
    flash(f"Curso {curso['codigo']} excluído.", "success")
    return redirect(url_for("admin.painel"))


# ---------- atividades ----------


@bp.post("/cursos/<int:curso_id>/atividades")
@perfil_required("administrador")
def criar_atividade(curso_id: int):
    db = get_db()
    curso = _curso_ou_404(db, curso_id)
    titulo, erros = conteudo.validar_titulo_atividade(request.form.get("titulo"))
    if erros:
        _avisar_erros(erros)
        return _volta(curso_id, "#atividades")
    conteudo.criar_atividade(db, curso_id, titulo)
    registrar(db, "atividade_criada", g.usuario["id"], f"curso={curso['codigo']}")
    db.commit()
    flash("Atividade adicionada.", "success")
    return _volta(curso_id, "#atividades")


@bp.post("/atividades/<int:atividade_id>/editar")
@perfil_required("administrador")
def editar_atividade(atividade_id: int):
    db = get_db()
    atividade = conteudo.obter_atividade(db, atividade_id) or abort(404)
    titulo, erros = conteudo.validar_titulo_atividade(request.form.get("titulo"))
    if erros:
        _avisar_erros(erros)
        return _volta(atividade["curso_id"], "#atividades")
    conteudo.renomear_atividade(db, atividade_id, titulo)
    curso = _curso_ou_404(db, atividade["curso_id"])
    registrar(db, "atividade_editada", g.usuario["id"], f"curso={curso['codigo']}")
    db.commit()
    flash("Atividade renomeada.", "success")
    return _volta(curso["id"], "#atividades")


@bp.post("/atividades/<int:atividade_id>/remover")
@perfil_required("administrador")
def remover_atividade(atividade_id: int):
    db = get_db()
    atividade = conteudo.obter_atividade(db, atividade_id) or abort(404)
    curso = _curso_ou_404(db, atividade["curso_id"])
    try:
        conteudo.remover_atividade(db, atividade_id)
    except conteudo.ConteudoInvalidoError as erro:
        flash(str(erro), "warning")
        return _volta(curso["id"], "#atividades")
    registrar(db, "atividade_removida", g.usuario["id"], f"curso={curso['codigo']}")
    db.commit()
    flash("Atividade removida.", "success")
    return _volta(curso["id"], "#atividades")


# ---------- questões e respostas ----------


@bp.post("/cursos/<int:curso_id>/questoes")
@perfil_required("administrador")
def criar_questao(curso_id: int):
    db = get_db()
    curso = _curso_ou_404(db, curso_id)
    questao, erros = conteudo.validar_questao(request.form)
    if erros:
        _avisar_erros(erros)
        return _volta(curso_id, "#questoes")
    conteudo.criar_questao(db, curso_id, questao)
    registrar(db, "questao_criada", g.usuario["id"], f"curso={curso['codigo']}")
    db.commit()
    flash("Questão adicionada.", "success")
    return _volta(curso_id, "#questoes")


@bp.post("/questoes/<int:questao_id>/editar")
@perfil_required("administrador")
def editar_questao(questao_id: int):
    db = get_db()
    atual = conteudo.obter_questao(db, questao_id) or abort(404)
    curso = _curso_ou_404(db, atual["curso_id"])
    questao, erros = conteudo.validar_questao(request.form)
    if erros:
        _avisar_erros(erros)
        return _volta(curso["id"], "#questoes")
    conteudo.atualizar_questao(db, questao_id, questao)
    registrar(db, "questao_editada", g.usuario["id"], f"curso={curso['codigo']}")
    db.commit()
    flash("Questão salva.", "success")
    return _volta(curso["id"], "#questoes")


@bp.post("/questoes/<int:questao_id>/remover")
@perfil_required("administrador")
def remover_questao(questao_id: int):
    db = get_db()
    atual = conteudo.obter_questao(db, questao_id) or abort(404)
    curso = _curso_ou_404(db, atual["curso_id"])
    conteudo.remover_questao(db, questao_id)
    registrar(db, "questao_removida", g.usuario["id"], f"curso={curso['codigo']}")
    db.commit()
    flash("Questão removida.", "success")
    return _volta(curso["id"], "#questoes")


# ---------- links de vídeo ----------


@bp.post("/cursos/<int:curso_id>/links")
@perfil_required("administrador")
def criar_link(curso_id: int):
    db = get_db()
    curso = _curso_ou_404(db, curso_id)
    link, erros = conteudo.validar_link(request.form.get("titulo"), request.form.get("url"))
    if erros:
        _avisar_erros(erros)
        return _volta(curso_id, "#links")
    conteudo.criar_link(db, curso_id, link)
    registrar(db, "link_adicionado", g.usuario["id"], f"curso={curso['codigo']}")
    db.commit()
    flash("Link adicionado.", "success")
    return _volta(curso_id, "#links")


@bp.post("/links/<int:link_id>/remover")
@perfil_required("administrador")
def remover_link(link_id: int):
    db = get_db()
    link = conteudo.obter_link(db, link_id) or abort(404)
    curso = _curso_ou_404(db, link["curso_id"])
    conteudo.remover_link(db, link_id)
    registrar(db, "link_removido", g.usuario["id"], f"curso={curso['codigo']}")
    db.commit()
    flash("Link removido.", "success")
    return _volta(curso["id"], "#links")


# ---------- eventos e banco de dados ----------


@bp.get("/eventos")
@perfil_required("administrador")
def eventos():
    pagina = request.args.get("pagina", default=1, type=int)
    linhas, pagina, paginas, total = logs.listar_eventos(get_db(), pagina)
    return render_template(
        "admin_eventos.html", eventos=linhas, pagina=pagina, paginas=paginas, total=total
    )


@bp.get("/banco")
@perfil_required("administrador")
def banco_de_dados():
    return render_template(
        "admin_banco.html",
        tabelas=banco.resumo_das_tabelas(get_db()),
        arquivo=current_app.config["DATABASE"],
    )


@bp.get("/banco/<tabela>")
@perfil_required("administrador")
def tabela_do_banco(tabela: str):
    pagina = request.args.get("pagina", default=1, type=int)
    try:
        colunas, linhas, pagina, paginas, total = banco.amostra(get_db(), tabela, pagina)
    except KeyError:
        abort(404)
    return render_template(
        "admin_tabela.html",
        tabela=tabela,
        colunas=colunas,
        linhas=linhas,
        pagina=pagina,
        paginas=paginas,
        total=total,
    )
