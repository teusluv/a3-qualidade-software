"""Caixa-branca: regra de novo início de curso (CA-03, A-08)."""

from datetime import date

import pytest

from app.services.cursos import curso_aceita_novo_inicio

HOJE = date(2026, 11, 16)


@pytest.mark.parametrize(
    ("status", "inicio", "fim", "esperado"),
    [
        ("ativo", "2026-01-01", "2026-12-31", True),
        ("ativo", "2026-11-16", "2026-12-31", True),  # começa hoje
        ("ativo", "2026-01-01", "2026-11-16", True),  # termina hoje
        ("ativo", "2026-11-17", "2026-12-31", False),  # ainda não começou
        ("ativo", "2026-01-01", "2026-11-15", False),  # já terminou
        ("suspenso", "2026-01-01", "2026-12-31", False),
        ("arquivado", "2026-01-01", "2026-12-31", False),
    ],
)
def test_curso_aceita_novo_inicio(status, inicio, fim, esperado):
    assert curso_aceita_novo_inicio(status, inicio, fim, HOJE) is esperado
