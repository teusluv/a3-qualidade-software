"""Acesso ao banco SQLite."""

import sqlite3
from pathlib import Path

from flask import current_app, g

SCHEMA = Path(__file__).parent / "schema.sql"


def get_db() -> sqlite3.Connection:
    """Devolve a conexão da requisição atual (uma por requisição)."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_erro=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    """Cria as tabelas, se ainda não existirem."""
    db = get_db()
    db.executescript(SCHEMA.read_text(encoding="utf-8"))
    db.commit()
