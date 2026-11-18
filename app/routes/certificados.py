"""Emissão e download do certificado (RF-07) e consulta pública (RF-08, T-05)."""

from flask import (
    Blueprint,
    Response,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)

from app.auth import login_required
from app.db import get_db
from app.services import certificado
from app.services.logs import registrar

bp = Blueprint("certificados", __name__)


@bp.post("/cursos/<int:curso_id>/certificado")
@login_required
def emitir(curso_id: int):
    db = get_db()
    try:
        emitido, _criado_agora = certificado.emitir_certificado(db, g.usuario["id"], curso_id)
    except certificado.ErroEmissao as erro:
        registrar(db, "emissao_negada", g.usuario["id"], f"curso_id={curso_id}")
        db.commit()
        flash(str(erro), "warning")
        return redirect(url_for("cursos.detalhe", curso_id=curso_id))
    return redirect(url_for("certificados.baixar_pdf", certificado_id=emitido["id"]))


@bp.get("/certificados/<int:certificado_id>/pdf")
@login_required
def baixar_pdf(certificado_id: int):
    dados = certificado.obter_certificado_para_pdf(get_db(), certificado_id)
    # RNF-06: o colaborador só acessa o próprio certificado; o administrador acessa todos.
    if dados is None or (
        dados["usuario_id"] != g.usuario["id"] and g.usuario["perfil"] != "administrador"
    ):
        abort(404)
    pdf = certificado.gerar_pdf(dados)
    return Response(
        pdf,
        mimetype="application/pdf",
        headers={"Content-Disposition": f'inline; filename="certificado-{dados["codigo"]}.pdf"'},
    )


@bp.get("/verificar")
def verificar():
    """Consulta pública, sem login. Mostra só o mínimo e nunca devolve o que foi digitado."""
    codigo = request.args.get("codigo")
    if codigo is None:
        return render_template("verificar.html", estado="inicial")

    codigo = codigo.strip()
    if not codigo:
        return render_template("verificar.html", estado="vazio"), 400
    if not certificado.codigo_tem_formato_valido(codigo):
        return render_template("verificar.html", estado="formato_invalido"), 400

    encontrado = certificado.consultar_publico(get_db(), codigo)
    if encontrado is None:
        return render_template("verificar.html", estado="nao_encontrado"), 404
    return render_template("verificar.html", estado="autentico", dados=encontrado)
