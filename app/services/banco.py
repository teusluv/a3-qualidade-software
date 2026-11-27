"""Visualização somente leitura do banco de dados, para o administrador.

O nome da tabela vem da URL, então só é aceito se existir de verdade no banco (lista fechada
lida de `sqlite_master`). Os nomes de tabela e de coluna usados nas consultas vêm sempre dessa
lista, nunca direto do usuário (por isso os avisos B608 do bandit estão marcados com `nosec`).
A coluna `senha_hash` nunca é mostrada.
"""

from app.services.logs import paginar

COLUNAS_OCULTAS = {"senha_hash"}
LINHAS_POR_PAGINA = 20


def nomes_das_tabelas(db) -> list[str]:
    linhas = db.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' "
        "ORDER BY name"
    )
    return [linha["name"] for linha in linhas]


def colunas_da_tabela(db, tabela: str) -> list[dict]:
    """Só chamar com um nome já validado por `nomes_das_tabelas`."""
    return [
        {
            "nome": c["name"],
            "tipo": c["type"],
            "chave": bool(c["pk"]),
            "obrigatoria": bool(c["notnull"]),
        }
        for c in db.execute(f'PRAGMA table_info("{tabela}")')
    ]


def resumo_das_tabelas(db) -> list[dict]:
    resumo = []
    for nome in nomes_das_tabelas(db):
        total = db.execute(f'SELECT COUNT(*) FROM "{nome}"').fetchone()[0]  # nosec B608
        resumo.append({"nome": nome, "total": total, "colunas": colunas_da_tabela(db, nome)})
    return resumo


def amostra(db, tabela: str, pagina: int = 1):
    """Linhas da tabela, por página. Devolve (colunas, linhas, página, páginas, total)."""
    if tabela not in nomes_das_tabelas(db):
        raise KeyError(tabela)
    colunas = [c["nome"] for c in colunas_da_tabela(db, tabela)]
    total = db.execute(f'SELECT COUNT(*) FROM "{tabela}"').fetchone()[0]  # nosec B608
    pagina, paginas, deslocamento = paginar(total, pagina, LINHAS_POR_PAGINA)
    selecao = ", ".join(
        "'(oculto)'" if c in COLUNAS_OCULTAS else f'"{c}"' for c in colunas
    )
    linhas = db.execute(
        f'SELECT {selecao} FROM "{tabela}" ORDER BY rowid LIMIT ? OFFSET ?',  # nosec B608
        (LINHAS_POR_PAGINA, deslocamento),
    ).fetchall()
    return colunas, [tuple(linha) for linha in linhas], pagina, paginas, total
