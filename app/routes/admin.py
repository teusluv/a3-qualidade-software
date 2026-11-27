"""Área restrita ao administrador: cursos, materiais e eventos (CT-02, RF-09, CA-16)."""

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
from app.config import NOTA_MINIMA_PADRAO
from app.db import get_db
from app.services import cadastro, logs, materiais
from app.services.logs import registrar

bp = Blueprint("admin", __name__, url_prefix="/admin")

STATUS_VALIDOS = ("ativo", "suspenso", "arquivado")


def _setores(db) -> list[str]:
    linhas = db.execute("SELECT DISTINCT setor FROM usuario ORDER BY setor").fetchall()
    return [linha["setor"] for linha in linhas]


def _contexto(db, valores=None, erros=None) -> dict:
    cursos = db.execute(
        "SELECT id, codigo, titulo, status, data_inicio, data_fim FROM curso ORDER BY codigo"
    ).fetchall()
    eventos, _pagina, _paginas, total_eventos = logs.listar_eventos(db, 1)
    return {
        "cursos": cursos,
        "codigos_usados": [c["codigo"] for c in cursos],
        "eventos": eventos,
        "total_eventos": total_eventos,
        "por_pagina": logs.EVENTOS_POR_PAGINA,
        "status_validos": STATUS_VALIDOS,
        "status_novo": cadastro.STATUS_NOVO,
        "setores": _setores(db),
        "valores": valores or {},
        "erros": erros or [],
        "nota_minima_padrao": NOTA_MINIMA_PADRAO,
    }


@bp.get("/")
@perfil_required("administrador")
def painel():
    return render_template("admin.html", **_contexto(get_db()))


@bp.post("/cursos")
@perfil_required("administrador")
def criar_curso():
    db = get_db()
    dados, erros = cadastro.validar_curso(request.form, set(_setores(db)))
    if not erros and cadastro.codigo_existe(db, dados["codigo"]):
        erros.append("Código: já existe um curso com este código.")
    if erros:
        return render_template("admin.html", **_contexto(db, request.form, erros)), 400

    novo_id = cadastro.criar_curso(db, dados)
    registrar(db, "curso_criado", g.usuario["id"], f"curso={dados['codigo']}")
    db.commit()
    flash(f"Curso {dados['codigo']} cadastrado. Complete o conteúdo abaixo.", "success")
    return redirect(url_for("gestao.curso", curso_id=novo_id))


@bp.post("/cursos/<int:curso_id>/status")
@perfil_required("administrador")
def alterar_status(curso_id: int):
    novo_status = request.form.get("status", "")
    if novo_status not in STATUS_VALIDOS:
        abort(400)
    db = get_db()
    curso = db.execute("SELECT codigo FROM curso WHERE id = ?", (curso_id,)).fetchone()
    if curso is None:
        abort(404)
    db.execute("UPDATE curso SET status = ? WHERE id = ?", (novo_status, curso_id))
    detalhe = f"curso={curso['codigo']} {novo_status}"
    registrar(db, "curso_status_alterado", g.usuario["id"], detalhe)
    db.commit()
    flash(f"Curso {curso['codigo']} agora está {novo_status}.", "success")
    return redirect(url_for("admin.painel"))


@bp.post("/cursos/<int:curso_id>/materiais")
@perfil_required("administrador")
def enviar_material(curso_id: int):
    db = get_db()
    curso = db.execute("SELECT codigo FROM curso WHERE id = ?", (curso_id,)).fetchone()
    if curso is None:
        abort(404)
    try:
        materiais.salvar_material(
            db,
            current_app.config["UPLOAD_FOLDER"],
            curso_id,
            request.files.get("arquivo"),
            g.usuario["id"],
        )
    except materiais.MaterialInvalidoError as erro:
        flash(str(erro), "warning")
        return redirect(url_for("gestao.curso", curso_id=curso_id) + "#material")
    registrar(db, "material_enviado", g.usuario["id"], f"curso={curso['codigo']}")
    db.commit()
    flash(f"Material anexado ao curso {curso['codigo']}.", "success")
    return redirect(url_for("gestao.curso", curso_id=curso_id) + "#material")


@bp.post("/materiais/<int:material_id>/remover")
@perfil_required("administrador")
def remover_material(material_id: int):
    db = get_db()
    material = db.execute("SELECT curso_id FROM material WHERE id = ?", (material_id,)).fetchone()
    if material is None:
        abort(404)
    materiais.remover_material(db, current_app.config["UPLOAD_FOLDER"], material_id)
    registrar(db, "material_removido", g.usuario["id"], f"material={material_id}")
    db.commit()
    flash("Material removido.", "success")
    return redirect(url_for("gestao.curso", curso_id=material["curso_id"]) + "#material")
