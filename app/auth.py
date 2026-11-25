
"""Autenticação, sessão e controle de acesso por perfil
(RF-01, RNF-06, RNF-07).
"""

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
    TAMANHO_MAXIMO_CAMPO_LOGIN,
    MAX_FALHAS_POR_MATRICULA,
    MAX_FALHAS_POR_ORIGEM,
)
from app.db import get_db
from app.services.logs import registrar

bp = Blueprint("auth", __name__)

MENSAGEM_LOGIN_INVALIDO = "Matrícula ou senha inválidas."
MENSAGEM_LOGIN_BLOQUEADO = (
    "Muitas tentativas de acesso. Tente novamente mais tarde."
)


class LoginForm(FlaskForm):
    # Não revela qual campo está incorreto (CA-01).
    matricula = StringField("Matrícula")
    senha = PasswordField("Senha")


def _estado_falhas():
    """Mantém os contadores isolados por instância da aplicação."""
    return current_app.extensions.setdefault(
        "controle_falhas_login",
        {
            "matriculas": {},
            "origens": {},
        },
    )


def _chave_matricula(matricula):
    """Normaliza a matrícula usada no controle de tentativas."""
    return matricula or "<vazia>"


def _chave_origem():
    """Identifica a origem da requisição."""
    return request.remote_addr or "<origem_desconhecida>"


def _esta_bloqueado(matricula):
    estado = _estado_falhas()

    falhas_matricula = estado["matriculas"].get(
        _chave_matricula(matricula), 0
    )
    falhas_origem = estado["origens"].get(_chave_origem(), 0)

    return (
        falhas_matricula >= MAX_FALHAS_POR_MATRICULA
        or falhas_origem >= MAX_FALHAS_POR_ORIGEM
    )


def _registrar_falha(matricula):
    """Incrementa os contadores por matrícula e por origem."""
    estado = _estado_falhas()

    chave = _chave_matricula(matricula)
    origem = _chave_origem()

    estado["matriculas"][chave] = (
        estado["matriculas"].get(chave, 0) + 1
    )

    estado["origens"][origem] = (
        estado["origens"].get(origem, 0) + 1
    )


def _limpar_falhas(matricula):
    """Limpa o contador individual após autenticação bem-sucedida."""
    estado = _estado_falhas()
    estado["matriculas"].pop(_chave_matricula(matricula), None)


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
    """Permite o acesso somente aos perfis informados."""

    def decorador(view):
        @wraps(view)
        def envolvida(*args, **kwargs):
            if g.usuario is None:
                return redirect(url_for("auth.login"))

            if g.usuario["perfil"] not in perfis:
                db = get_db()
                registrar(
                    db,
                    "acesso_negado",
                    g.usuario["id"],
                    request.path,
                )
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
        .execute(
            "SELECT id, senha_hash FROM usuario WHERE matricula = ?",
            (matricula,),
        )
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

        # Verifica o bloqueio antes de tentar autenticar.
        if _esta_bloqueado(matricula):
            db = get_db()
            registrar(db, "login_bloqueado")
            db.commit()

            formulario_limpo = LoginForm(formdata=None)

            return (
                render_template(
                    "login.html",
                    form=formulario_limpo,
                    erro=MENSAGEM_LOGIN_BLOQUEADO,
                ),
                429,
            )

        autenticado_id, usuario_conhecido_id = _autenticar(
            matricula,
            senha,
        )

        db = get_db()

        if autenticado_id is None:
            _registrar_falha(matricula)

            registrar(
                db,
                "login_falha",
                usuario_conhecido_id,
            )
            db.commit()

            formulario_limpo = LoginForm(formdata=None)

            return (
                render_template(
                    "login.html",
                    form=formulario_limpo,
                    erro=MENSAGEM_LOGIN_INVALIDO,
                ),
                401,
            )

        # Login válido: limpa o contador individual.
        _limpar_falhas(matricula)

        session.clear()
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
