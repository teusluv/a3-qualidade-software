
"""Autenticação, sessão e controle de acesso por perfil (RF-01, RNF-06, RNF-07)."""

from functools import wraps
from time import monotonic

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
    MAX_FALHAS_POR_MATRICULA,
    MAX_FALHAS_POR_ORIGEM,
    TAMANHO_MAXIMO_CAMPO_LOGIN,
)
from app.db import get_db
from app.services.logs import registrar

bp = Blueprint("auth", __name__)

MENSAGEM_LOGIN_INVALIDO = "Matrícula ou senha inválidas."
MENSAGEM_LOGIN_BLOQUEADO = (
    "Muitas tentativas de acesso. Tente novamente mais tarde."
)

JANELA_FALHAS_SEGUNDOS = 10 * 60
TEMPO_BLOQUEIO_SEGUNDOS = 5 * 60


class LoginForm(FlaskForm):
    matricula = StringField("Matrícula")
    senha = PasswordField("Senha")


def _estado_falhas():
    """Mantém os contadores isolados por instância da aplicação."""
    return current_app.extensions.setdefault(
        "controle_falhas_login",
        {"matriculas": {}, "origens": {}},
    )


def _chave_matricula(matricula):
    return matricula or "<vazia>"


def _chave_origem():
    return request.remote_addr or "<origem_desconhecida>"


def _consultar_falhas(contadores, chave, agora):
    """Remove falhas antigas e devolve o registro atual."""
    registro = contadores.get(chave)

    if registro is None:
        return {"falhas": [], "bloqueado_ate": 0.0}

    registro["falhas"] = [
        instante
        for instante in registro["falhas"]
        if agora - instante <= JANELA_FALHAS_SEGUNDOS
    ]

    if agora >= registro["bloqueado_ate"]:
        registro["bloqueado_ate"] = 0.0

    if not registro["falhas"] and not registro["bloqueado_ate"]:
        contadores.pop(chave, None)
        return {"falhas": [], "bloqueado_ate": 0.0}

    return registro


def _esta_bloqueado(matricula):
    estado = _estado_falhas()
    agora = monotonic()

    registro_matricula = _consultar_falhas(
        estado["matriculas"], _chave_matricula(matricula), agora
    )
    registro_origem = _consultar_falhas(
        estado["origens"], _chave_origem(), agora
    )

    return (
        agora < registro_matricula["bloqueado_ate"]
        or agora < registro_origem["bloqueado_ate"]
    )


def _registrar_falha(matricula):
    estado = _estado_falhas()
    agora = monotonic()

    for contadores, chave, limite in (
        (
            estado["matriculas"],
            _chave_matricula(matricula),
            MAX_FALHAS_POR_MATRICULA,
        ),
        (
            estado["origens"],
            _chave_origem(),
            MAX_FALHAS_POR_ORIGEM,
        ),
    ):
        registro = _consultar_falhas(contadores, chave, agora)
        registro["falhas"].append(agora)

        if len(registro["falhas"]) >= limite:
            registro["bloqueado_ate"] = agora + TEMPO_BLOQUEIO_SEGUNDOS

        contadores[chave] = registro


def _limpar_falhas(matricula):
    """Limpa somente as falhas individuais após autenticação válida."""
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
                "SELECT id, matricula, nome, perfil, setor FROM usuario "
                "WHERE id = ? AND ativo = 1",
                (usuario_id,),
            )
            .fetchone()
        )

        if g.usuario is None:
            session.clear()


def login_required(view):
    @wraps(view)
    def envolvida(*args, **kwargs):
        if g.usuario is None:
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return envolvida


def perfil_required(*perfis: str):
    """Permite o acesso só aos perfis informados."""

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
    """Devolve (id autenticado ou None, id conhecido ou None)."""
    if not matricula or not senha:
        return None, None

    if max(len(matricula), len(senha)) > TAMANHO_MAXIMO_CAMPO_LOGIN:
        return None, None

    usuario = (
        get_db()
        .execute(
            "SELECT id, senha_hash, ativo FROM usuario WHERE matricula = ?",
            (matricula,),
        )
        .fetchone()
    )

    if usuario is None:
        return None, None

    senha_correta = check_password_hash(usuario["senha_hash"], senha)

    if not senha_correta or not usuario["ativo"]:
        return None, usuario["id"]

    return usuario["id"], usuario["id"]


@bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        matricula = (form.matricula.data or "").strip()
        senha = form.senha.data or ""

        if _esta_bloqueado(matricula):
            db = get_db()
            registrar(db, "login_bloqueado")
            db.commit()

            return (
                render_template(
                    "login.html",
                    form=LoginForm(formdata=None),
                    erro=MENSAGEM_LOGIN_BLOQUEADO,
                ),
                429,
            )

        autenticado_id, usuario_conhecido_id = _autenticar(matricula, senha)
        db = get_db()

        if autenticado_id is None:
            _registrar_falha(matricula)
            registrar(db, "login_falha", usuario_conhecido_id)
            db.commit()

            return (
                render_template(
                    "login.html",
                    form=LoginForm(formdata=None),
                    erro=MENSAGEM_LOGIN_INVALIDO,
                ),
                401,
            )

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
