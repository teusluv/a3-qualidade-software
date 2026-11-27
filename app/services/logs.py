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


EVENTOS_POR_PAGINA = 20


def paginar(total: int, pagina: int, por_pagina: int = EVENTOS_POR_PAGINA) -> tuple[int, int, int]:
    """Devolve (página corrigida, total de páginas, deslocamento); ajusta página fora do limite."""
    paginas = max(1, -(-total // por_pagina))  # divisão para cima
    pagina = min(max(1, pagina), paginas)
    return pagina, paginas, (pagina - 1) * por_pagina


def listar_eventos(db, pagina: int = 1, por_pagina: int = EVENTOS_POR_PAGINA):
    """Eventos do mais novo para o mais antigo, por página. Nada é apagado."""
    total = db.execute("SELECT COUNT(*) FROM log").fetchone()[0]
    pagina, paginas, deslocamento = paginar(total, pagina, por_pagina)
    linhas = db.execute(
        "SELECT l.criado_em, l.acao, l.detalhe, u.matricula "
        "FROM log l LEFT JOIN usuario u ON u.id = l.usuario_id "
        "ORDER BY l.id DESC LIMIT ? OFFSET ?",
        (por_pagina, deslocamento),
    ).fetchall()
    return linhas, pagina, paginas, total
