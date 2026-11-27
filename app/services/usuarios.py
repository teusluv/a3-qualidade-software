"""Contas de usuário criadas pelo administrador (RF-01).

`validar_usuario` e `validar_senha` são funções puras. As demais recebem `db` e NÃO fazem commit.
A senha nunca é guardada nem registrada em texto: só o hash.
"""

import re
from collections.abc import Mapping

from werkzeug.security import check_password_hash, generate_password_hash

PERFIS = ("colaborador", "administrador")
PADRAO_MATRICULA = re.compile(r"^[0-9]{3,10}$")
TAMANHO_MIN_SENHA = 8
TAMANHO_MAX_SENHA = 64


def validar_senha(senha) -> list[str]:
    senha = senha or ""
    erros = []
    if not TAMANHO_MIN_SENHA <= len(senha) <= TAMANHO_MAX_SENHA:
        erros.append(f"Senha: use de {TAMANHO_MIN_SENHA} a {TAMANHO_MAX_SENHA} caracteres.")
    elif not (re.search(r"[A-Za-z]", senha) and re.search(r"[0-9]", senha)):
        erros.append("Senha: use pelo menos uma letra e um número.")
    return erros


def validar_usuario(dados: Mapping) -> tuple[dict, list[str]]:
    erros: list[str] = []
    matricula = (dados.get("matricula") or "").strip()
    if not PADRAO_MATRICULA.match(matricula):
        erros.append("Matrícula: use de 3 a 10 números, sem letras nem espaços.")
    nome = " ".join((dados.get("nome") or "").split())
    if not 3 <= len(nome) <= 100:
        erros.append("Nome: informe de 3 a 100 caracteres.")
    setor = " ".join((dados.get("setor") or "").split())
    if not 2 <= len(setor) <= 40:
        erros.append("Setor: informe de 2 a 40 caracteres.")
    perfil = (dados.get("perfil") or "").strip()
    if perfil not in PERFIS:
        erros.append("Perfil: escolha colaborador ou administrador.")
    erros.extend(validar_senha(dados.get("senha")))
    limpo = {"matricula": matricula, "nome": nome, "setor": setor, "perfil": perfil}
    return limpo, erros


def matricula_existe(db, matricula: str) -> bool:
    linha = db.execute("SELECT 1 FROM usuario WHERE matricula = ?", (matricula,)).fetchone()
    return linha is not None


class ContaInvalidaError(Exception):
    """A operação sobre a conta foi recusada; a mensagem pode ser mostrada ao usuário."""


def listar_usuarios(db):
    return db.execute(
        "SELECT u.id, u.matricula, u.nome, u.perfil, u.setor, u.ativo, "
        "(EXISTS (SELECT 1 FROM inscricao WHERE usuario_id = u.id) "
        " OR EXISTS (SELECT 1 FROM certificado WHERE usuario_id = u.id) "
        " OR EXISTS (SELECT 1 FROM log WHERE usuario_id = u.id)) AS tem_historico "
        "FROM usuario u ORDER BY u.perfil DESC, u.nome"
    ).fetchall()


def obter_usuario(db, usuario_id: int):
    return db.execute(
        "SELECT id, matricula, nome, perfil, setor, ativo FROM usuario WHERE id = ?", (usuario_id,)
    ).fetchone()


def contar_administradores_ativos(db) -> int:
    return db.execute(
        "SELECT COUNT(*) FROM usuario WHERE perfil = 'administrador' AND ativo = 1"
    ).fetchone()[0]


def tem_historico(db, usuario_id: int) -> bool:
    """A conta já fez algo (iniciou curso, tem certificado ou aparece nos eventos)?"""
    linha = db.execute(
        "SELECT (EXISTS (SELECT 1 FROM inscricao WHERE usuario_id = :id) "
        "        OR EXISTS (SELECT 1 FROM certificado WHERE usuario_id = :id) "
        "        OR EXISTS (SELECT 1 FROM log WHERE usuario_id = :id))",
        {"id": usuario_id},
    ).fetchone()
    return linha[0] == 1


def _garantir_outro_administrador(db, alvo) -> None:
    e_admin_ativo = alvo["perfil"] == "administrador" and alvo["ativo"]
    if e_admin_ativo and contar_administradores_ativos(db) <= 1:
        raise ContaInvalidaError("É preciso manter pelo menos um administrador ativo.")


def alterar_situacao(db, alvo_id: int, ativar: bool, ator_id: int) -> None:
    """Desativa ou reativa uma conta. O histórico dela é preservado. Quem chama faz o commit."""
    alvo = obter_usuario(db, alvo_id)
    if alvo is None:
        raise LookupError(alvo_id)
    if not ativar:
        if alvo_id == ator_id:
            raise ContaInvalidaError("Você não pode desativar a sua própria conta.")
        _garantir_outro_administrador(db, alvo)
    db.execute("UPDATE usuario SET ativo = ? WHERE id = ?", (1 if ativar else 0, alvo_id))


def excluir_usuario(db, alvo_id: int, ator_id: int) -> None:
    """Exclui só conta sem nenhum histórico (ex.: criada por engano). Quem chama faz o commit."""
    alvo = obter_usuario(db, alvo_id)
    if alvo is None:
        raise LookupError(alvo_id)
    if alvo_id == ator_id:
        raise ContaInvalidaError("Você não pode excluir a sua própria conta.")
    if tem_historico(db, alvo_id):
        raise ContaInvalidaError(
            "Esta conta tem histórico (cursos, certificados ou eventos) e não pode ser excluída. "
            "Desative-a: ela deixa de entrar e o histórico é preservado."
        )
    _garantir_outro_administrador(db, alvo)
    db.execute("DELETE FROM usuario WHERE id = ?", (alvo_id,))


def validar_troca_senha(senha_hash_atual: str, atual, nova, confirmacao) -> list[str]:
    """Regras da troca de senha feita pela própria pessoa."""
    if not check_password_hash(senha_hash_atual, atual or ""):
        return ["Senha atual: não confere."]
    erros = validar_senha(nova)
    if not erros and (nova or "") == (atual or ""):
        erros.append("Nova senha: precisa ser diferente da atual.")
    if not erros and (nova or "") != (confirmacao or ""):
        erros.append("Confirmação: a nova senha e a confirmação não são iguais.")
    return erros


def listar_setores(db) -> list[str]:
    linhas = db.execute("SELECT DISTINCT setor FROM usuario ORDER BY setor").fetchall()
    return [linha["setor"] for linha in linhas]


def criar_usuario(db, usuario: dict, senha: str) -> int:
    cursor = db.execute(
        "INSERT INTO usuario (matricula, nome, senha_hash, perfil, setor) VALUES (?, ?, ?, ?, ?)",
        (usuario["matricula"], usuario["nome"], generate_password_hash(senha),
         usuario["perfil"], usuario["setor"]),
    )
    return cursor.lastrowid


def redefinir_senha(db, usuario_id: int, senha: str) -> bool:
    novo_hash = generate_password_hash(senha)
    cursor = db.execute("UPDATE usuario SET senha_hash = ? WHERE id = ?", (novo_hash, usuario_id))
    return cursor.rowcount == 1
