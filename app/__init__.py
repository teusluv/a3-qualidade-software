"""Portal de Treinamentos e Certificados: application factory."""

from pathlib import Path

from flask import Flask, render_template, request, url_for
from flask_wtf import CSRFProtect

from app import auth, db
from app.config import Config
from app.routes import admin, certificados, conta, cursos, gestao, usuarios
from app.services.certificado import formatar_data

csrf = CSRFProtect()


def _url_voltar() -> str:
    """Página anterior, só se for do próprio sistema; senão, o início."""
    anterior = request.referrer
    if anterior and anterior.startswith(request.host_url):
        return anterior
    return url_for("cursos.catalogo")


def _pagina_de_erro(codigo: int, mensagem: str):
    voltar = _url_voltar()
    return render_template("erro.html", codigo=codigo, mensagem=mensagem, voltar_url=voltar), codigo


def _preparar_banco(app: Flask) -> None:
    """Cria as tabelas se faltarem e recusa um banco de versão anterior, com instrução clara."""
    with app.app_context():
        db.init_db()
        conexao = db.get_db()
        db.migrar_banco(conexao)
        colunas = [linha["name"] for linha in conexao.execute("PRAGMA table_info(certificado)")]
        if "concluido_em" not in colunas:
            raise RuntimeError(
                "Banco de dados desatualizado. Apague a pasta 'instance' e rode: python seed.py"
            )
        sem_usuarios = conexao.execute("SELECT COUNT(*) FROM usuario").fetchone()[0] == 0
        if sem_usuarios and app.config.get("AVISAR_BANCO_VAZIO", True):
            app.logger.warning("Banco sem usuários. Rode: python seed.py")


def create_app(config_teste: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    app.config["DATABASE"] = str(Path(app.instance_path) / "portal.db")
    app.config["UPLOAD_FOLDER"] = str(Path(app.instance_path) / "uploads")

    if config_teste:
        app.config.update(config_teste)

    csrf.init_app(app)
    app.teardown_appcontext(db.close_db)
    app.jinja_env.filters["data_br"] = formatar_data
    _preparar_banco(app)

    app.register_blueprint(auth.bp)
    app.register_blueprint(cursos.bp)
    app.register_blueprint(certificados.bp)
    app.register_blueprint(gestao.bp)
    app.register_blueprint(usuarios.bp)
    app.register_blueprint(conta.bp)
    app.register_blueprint(admin.bp)

    @app.errorhandler(403)
    def acesso_negado(_erro):
        return _pagina_de_erro(403, "Acesso negado.")

    @app.errorhandler(413)
    def arquivo_grande(_erro):
        mensagem = "Arquivo muito grande. O limite é de 20 MB."
        return _pagina_de_erro(413, mensagem)

    @app.errorhandler(500)
    def erro_interno(_erro):
        mensagem = "Ocorreu um erro inesperado. Tente novamente."
        return _pagina_de_erro(500, mensagem)

    @app.errorhandler(404)
    def nao_encontrado(_erro):
        return _pagina_de_erro(404, "Página não encontrada.")

    @app.after_request
    def adicionar_cabecalhos_seguranca(resposta):
        resposta.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net; "
            "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "frame-ancestors 'none'; "
            "object-src 'none'; "
            "base-uri 'self'"
        )
        resposta.headers["X-Frame-Options"] = "DENY"
        resposta.headers["X-Content-Type-Options"] = "nosniff"
        resposta.headers["Referrer-Policy"] = "no-referrer"
        resposta.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )

        if app.config.get("SESSION_COOKIE_SECURE"):
            resposta.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return resposta

    return app
