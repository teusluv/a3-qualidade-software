"""Registro de eventos (CA-16).

Regra: o log guarda o identificador do usuário, a ação e a data/hora. Nunca senha, CPF
ou e-mail. A função NÃO faz commit: quem chama decide, para poder gravar o log na mesma
transação da operação que ele descreve.
"""

from datetime import datetime


def agora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def registrar(db, acao: str, usuario_id: int | None = None, detalhe: str | None = None) -> None:
    db.execute(
        "INSERT INTO log (usuario_id, acao, detalhe, criado_em) VALUES (?, ?, ?, ?)",
        (usuario_id, acao, detalhe, agora()),
    )
