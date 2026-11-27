"""Contas de usuário: lista, criação e redefinição de senha, só para o administrador."""

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from app.auth import perfil_required
from app.db import get_db
from app.services import usuarios
from app.services.logs import registrar

bp = Blueprint("usuarios", __name__, url_prefix="/admin/usuarios")


def _pagina(db, valores=None, erros=None):
    return render_template(
        "admin_usuarios.html",
        usuarios=usuarios.listar_usuarios(db),
        setores=usuarios.listar_setores(db),
        perfis=usuarios.PERFIS,
        valores=valores or {},
        erros=erros or [],
        senha_min=usuarios.TAMANHO_MIN_SENHA,
    )


@bp.get("/")
@perfil_required("administrador")
def lista():
    return _pagina(get_db())


@bp.post("/")
@perfil_required("administrador")
def criar():
    db = get_db()
    dados, erros = usuarios.validar_usuario(request.form)
    if not erros and usuarios.matricula_existe(db, dados["matricula"]):
        erros.append("Matrícula: já existe uma conta com esta matrícula.")
    if erros:
        valores = {k: v for k, v in request.form.items() if k != "senha"}  # senha não volta à tela
        return _pagina(db, valores, erros), 400

    novo_id = usuarios.criar_usuario(db, dados, request.form["senha"])
    detalhe = f"usuario_id={novo_id} perfil={dados['perfil']}"
    registrar(db, "usuario_criado", g.usuario["id"], detalhe)
    db.commit()
    flash(f"Conta criada: {dados['nome']} (matrícula {dados['matricula']}).", "success")
    return redirect(url_for("usuarios.lista"))


@bp.post("/<int:usuario_id>/senha")
@perfil_required("administrador")
def redefinir_senha(usuario_id: int):
    db = get_db()
    senha = request.form.get("senha", "")
    erros = usuarios.validar_senha(senha)
    if erros:
        for erro in erros:
            flash(erro, "warning")
        return redirect(url_for("usuarios.lista"))
    if not usuarios.redefinir_senha(db, usuario_id, senha):
        abort(404)
    registrar(db, "senha_redefinida", g.usuario["id"], f"usuario_id={usuario_id}")
    db.commit()
    flash("Senha redefinida.", "success")
    return redirect(url_for("usuarios.lista"))


def _acao_sobre_conta(usuario_id: int, acao: str, mensagem_ok: str):
    """Desativar, reativar ou excluir: trata os recusos e registra o evento."""
    db = get_db()
    try:
        if acao == "excluir":
            usuarios.excluir_usuario(db, usuario_id, g.usuario["id"])
        else:
            usuarios.alterar_situacao(db, usuario_id, acao == "reativar", g.usuario["id"])
    except LookupError:
        abort(404)
    except usuarios.ContaInvalidaError as erro:
        flash(str(erro), "warning")
        return redirect(url_for("usuarios.lista"))
    registrar(db, f"usuario_{acao}", g.usuario["id"], f"usuario_id={usuario_id}")
    db.commit()
    flash(mensagem_ok, "success")
    return redirect(url_for("usuarios.lista"))


@bp.post("/<int:usuario_id>/desativar")
@perfil_required("administrador")
def desativar(usuario_id: int):
    aviso = "Conta desativada. O histórico foi preservado."
    return _acao_sobre_conta(usuario_id, "desativar", aviso)


@bp.post("/<int:usuario_id>/reativar")
@perfil_required("administrador")
def reativar(usuario_id: int):
    return _acao_sobre_conta(usuario_id, "reativar", "Conta reativada.")


@bp.post("/<int:usuario_id>/excluir")
@perfil_required("administrador")
def excluir(usuario_id: int):
    return _acao_sobre_conta(usuario_id, "excluir", "Conta excluída.")
