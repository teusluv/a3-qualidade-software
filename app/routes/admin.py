"""Área restrita ao administrador (CT-02, RF-09 mínimo, CA-16)."""

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from app.auth import perfil_required
from app.db import get_db
from app.services.logs import registrar

bp = Blueprint("admin", __name__, url_prefix="/admin")

STATUS_VALIDOS = ("ativo", "suspenso", "arquivado")


@bp.get("/")
@perfil_required("administrador")
def painel():
    db = get_db()
    cursos = db.execute(
        "SELECT id, codigo, titulo, status, data_inicio, data_fim FROM curso ORDER BY codigo"
    ).fetchall()
    logs = db.execute(
        "SELECT l.criado_em, l.acao, l.detalhe, u.matricula "
        "FROM log l LEFT JOIN usuario u ON u.id = l.usuario_id "
        "ORDER BY l.id DESC LIMIT 50"
    ).fetchall()
    return render_template("admin.html", cursos=cursos, logs=logs, status_validos=STATUS_VALIDOS)


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
