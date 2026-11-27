"""Conta da própria pessoa: troca de senha (qualquer usuário logado)."""

from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from app.auth import login_required
from app.db import get_db
from app.services import usuarios
from app.services.logs import registrar

bp = Blueprint("conta", __name__, url_prefix="/conta")


@bp.route("/senha", methods=["GET", "POST"])
@login_required
def senha():
    erros: list[str] = []
    if request.method == "POST":
        db = get_db()
        atual = db.execute(
            "SELECT senha_hash FROM usuario WHERE id = ?", (g.usuario["id"],)
        ).fetchone()
        erros = usuarios.validar_troca_senha(
            atual["senha_hash"],
            request.form.get("senha_atual"),
            request.form.get("senha_nova"),
            request.form.get("senha_confirmacao"),
        )
        if not erros:
            usuarios.redefinir_senha(db, g.usuario["id"], request.form["senha_nova"])
            registrar(db, "senha_alterada", g.usuario["id"])
            db.commit()
            flash("Senha alterada com sucesso.", "success")
            return redirect(url_for("cursos.catalogo"))
    pagina = render_template("conta_senha.html", erros=erros, senha_min=usuarios.TAMANHO_MIN_SENHA)
    return pagina, (400 if erros else 200)
