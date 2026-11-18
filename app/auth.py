"""Autenticação, sessão e controle de acesso por perfil (RF-01, RNF-06, RNF-07)."""

import time
from functools import wraps

from flask import (
    Blueprint,
    abort,
    current_app,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_wtf import FlaskForm
from werkzeug.security import check_password_hash
from wtforms import PasswordField, StringField

from app.config import (
    BLOQUEIO_MINUTOS,
    JANELA_FALHAS_MINUTOS,
    MAX_FALHAS_POR_MATRICULA,
    MAX_FALHAS_POR_ORIGEM,
    TAMANHO_MAXIMO_CAMPO_LOGIN,
)
from app.db import get_db
from app.services.logs import registrar

bp = Blueprint("auth", __name__)

MENSAGEM_LOGIN_INVALIDO = "Matrícula ou senha inválidas."
MENSAGEM_LOGIN_BLOQUEADO = (
    "Muitas tentativas seguidas. Aguarde alguns minutos e tente de novo."
)


def _placar():
    """Falhas recentes de login, por aplicação (D-02).

    Guardado na própria aplicação, e não em variável de módulo, para que cada aplicação
    criada por create_app comece limpa (os testes dependem disso).

    Limitação do protótipo: fica em memória, então vale por processo e zera ao reiniciar.
    Em produção, com mais de um processo, isso iria para Redis ou para o banco.
    """
    return current_app.extensions.setdefault("falhas_login", {})


def _recentes(chave: str, agora: float) -> list[float]:
    janela = JANELA_FALHAS_MINUTOS * 60
    falhas = [t for t in _placar().get(chave, []) if agora - t < janela]
    _placar()[chave] = falhas
    return falhas


def _esta_bloqueado(origem: str, matricula: str) -> bool:
    agora = time.time()
    bloqueio = BLOQUEIO_MINUTOS * 60
    por_matricula = _recentes(f"{origem}|{matricula}", agora)
    por_origem = _recentes(origem, agora)
    if len(por_matricula) >= MAX_FALHAS_POR_MATRICULA and agora - por_matricula[-1] < bloqueio:
        return True
    return len(por_origem) >= MAX_FALHAS_POR_ORIGEM and agora - por_origem[-1] < bloqueio


def _registrar_falha(origem: str, matricula: str) -> None:
    agora = time.time()
    for chave in (f"{origem}|{matricula}", origem):
        _placar().setdefault(chave, []).append(agora)


def _limpar_falhas(origem: str, matricula: str) -> None:
    _placar().pop(f"{origem}|{matricula}", None)
    _placar().pop(origem, None)


class LoginForm(FlaskForm):
    # Sem validadores de propósito: erro por campo revelaria qual deles está errado (CA-01).
    matricula = StringField("Matrícula")
    senha = PasswordField("Senha")


@bp.before_app_request
def carregar_usuario_logado() -> None:
    usuario_id = session.get("usuario_id")
    g.usuario = None
    if usuario_id is not None:
        g.usuario = (
            get_db()
            .execute(
                "SELECT id, matricula, nome, perfil, setor FROM usuario WHERE id = ?",
                (usuario_id,),
            )
            .fetchone()
        )


def login_required(view):
    @wraps(view)
    def envolvida(*args, **kwargs):
        if g.usuario is None:
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return envolvida


def perfil_required(*perfis: str):
    """Permite o acesso só aos perfis informados. A checagem é feita no servidor."""

    def decorador(view):
        @wraps(view)
        def envolvida(*args, **kwargs):
            if g.usuario is None:
                return redirect(url_for("auth.login"))
            if g.usuario["perfil"] not in perfis:
                db = get_db()
                registrar(db, "acesso_negado", g.usuario["id"], request.path)
                db.commit()
                abort(403)
            return view(*args, **kwargs)

        return envolvida

    return decorador


def _autenticar(matricula: str, senha: str):
    """Devolve (id autenticado ou None, id do usuário conhecido ou None)."""
    if not matricula or not senha:
        return None, None
    if max(len(matricula), len(senha)) > TAMANHO_MAXIMO_CAMPO_LOGIN:
        return None, None
    usuario = (
        get_db()
        .execute("SELECT id, senha_hash FROM usuario WHERE matricula = ?", (matricula,))
        .fetchone()
    )
    if usuario is None:
        return None, None
    if not check_password_hash(usuario["senha_hash"], senha):
        return None, usuario["id"]
    return usuario["id"], usuario["id"]


@bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        matricula = (form.matricula.data or "").strip()
        senha = form.senha.data or ""
        origem = request.remote_addr or "desconhecida"

        # D-02: antes de conferir a senha, barra quem já errou demais há pouco tempo.
        # A mensagem é a mesma para qualquer matrícula, para não revelar quais existem.
        if _esta_bloqueado(origem, matricula):
            db = get_db()
            registrar(db, "login_bloqueado", None)
            db.commit()
            return render_template("login.html", form=form, erro=MENSAGEM_LOGIN_BLOQUEADO), 429

        autenticado_id, usuario_conhecido_id = _autenticar(matricula, senha)

        db = get_db()
        if autenticado_id is None:
            _registrar_falha(origem, matricula)
            # O log não guarda o que foi digitado, só o usuário, se a matrícula existir.
            registrar(db, "login_falha", usuario_conhecido_id)
            db.commit()
            return render_template("login.html", form=form, erro=MENSAGEM_LOGIN_INVALIDO), 401

        _limpar_falhas(origem, matricula)
        session.clear()  # evita fixação de sessão
        session["usuario_id"] = autenticado_id
        session.permanent = True
        registrar(db, "login_sucesso", autenticado_id)
        db.commit()
        return redirect(url_for("cursos.catalogo"))

    return render_template("login.html", form=form, erro=None)


@bp.post("/logout")
def logout():
    if g.usuario is not None:
        db = get_db()
        registrar(db, "logout", g.usuario["id"])
        db.commit()
    session.clear()
    return redirect(url_for("auth.login"))
