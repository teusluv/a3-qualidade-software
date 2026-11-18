"""Portal de Treinamentos e Certificados: application factory."""

from pathlib import Path

from flask import Flask, render_template
from flask_wtf import CSRFProtect

from app import auth, db
from app.config import CABECALHOS_SEGURANCA, Config
from app.routes import admin, certificados, cursos
from app.services.certificado import formatar_data

csrf = CSRFProtect()


def _preparar_banco(app: Flask) -> None:
    """Cria as tabelas se faltarem e recusa um banco de versão anterior, com instrução clara."""
    with app.app_context():
        db.init_db()
        conexao = db.get_db()
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

    if config_teste:
        app.config.update(config_teste)

    csrf.init_app(app)
    app.teardown_appcontext(db.close_db)
    app.jinja_env.filters["data_br"] = formatar_data
    _preparar_banco(app)

    app.register_blueprint(auth.bp)
    app.register_blueprint(cursos.bp)
    app.register_blueprint(certificados.bp)
    app.register_blueprint(admin.bp)

    @app.after_request
    def aplicar_cabecalhos_de_seguranca(resposta):
        """RNF-07 / defeitos D-03 e D-04: cabeçalhos em toda resposta, inclusive erros."""
        for nome, valor in CABECALHOS_SEGURANCA.items():
            resposta.headers[nome] = valor
        # HSTS só faz sentido em HTTPS; em HTTP local o navegador ignora e pode atrapalhar.
        if app.config.get("SESSION_COOKIE_SECURE"):
            resposta.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return resposta

    @app.errorhandler(403)
    def acesso_negado(_erro):
        return render_template("erro.html", codigo=403, mensagem="Acesso negado."), 403

    @app.errorhandler(500)
    def erro_interno(_erro):
        mensagem = "Ocorreu um erro inesperado. Tente novamente."
        return render_template("erro.html", codigo=500, mensagem=mensagem), 500

    @app.errorhandler(404)
    def nao_encontrado(_erro):
        return render_template("erro.html", codigo=404, mensagem="Página não encontrada."), 404

    return app
