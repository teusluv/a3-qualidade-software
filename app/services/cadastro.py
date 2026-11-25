"""Cadastro de cursos pelo administrador (RF-09).

`validar_curso` é uma função pura (fácil de testar). Todo curso novo recebe as 4 atividades e as
10 questões-modelo do `seed_data`: não há tela para editar questões neste protótipo.
"""

import re
from collections.abc import Mapping
from datetime import date

from app.config import NOTA_MINIMA_PADRAO
from app.seed_data import adicionar_modelo_ao_curso

STATUS_NOVO = ("ativo", "suspenso")
PADRAO_CODIGO = re.compile(r"^[A-Za-z0-9]{1,10}$")


def _inteiro(valor, minimo: int, maximo: int) -> int | None:
    try:
        numero = int(str(valor).strip())
    except ValueError:
        return None
    return numero if minimo <= numero <= maximo else None


def _data(valor) -> date | None:
    try:
        return date.fromisoformat(str(valor).strip())
    except ValueError:
        return None


def validar_curso(dados: Mapping, setores_validos: set[str]) -> tuple[dict, list[str]]:
    """Devolve (dados limpos, lista de erros em português). Sem erros = pode gravar."""
    erros: list[str] = []

    codigo = (dados.get("codigo") or "").strip().upper()
    if not PADRAO_CODIGO.match(codigo):
        erros.append("Código: use de 1 a 10 letras ou números, sem espaços.")

    titulo = (dados.get("titulo") or "").strip()
    if not 3 <= len(titulo) <= 120:
        erros.append("Título: informe de 3 a 120 caracteres.")

    carga = _inteiro(dados.get("carga_horaria"), 1, 200)
    if carga is None:
        erros.append("Carga horária: informe um número de 1 a 200 horas.")

    nota = _inteiro(dados.get("nota_minima"), NOTA_MINIMA_PADRAO, 100)
    if nota is None:
        erros.append(f"Nota mínima: informe um número de {NOTA_MINIMA_PADRAO} a 100.")

    setor = (dados.get("setor") or "").strip() or None
    if setor is not None and setor not in setores_validos:
        erros.append("Setor: escolha um setor da lista ou deixe em 'Todos'.")

    status = (dados.get("status") or "").strip()
    if status not in STATUS_NOVO:
        erros.append("Situação: escolha ativo ou suspenso.")

    inicio, fim = _data(dados.get("data_inicio")), _data(dados.get("data_fim"))
    if inicio is None or fim is None:
        erros.append("Período: informe a data de início e a de fim.")
    elif fim < inicio:
        erros.append("Período: a data de fim não pode ser anterior à de início.")

    limpo = {
        "codigo": codigo,
        "titulo": titulo,
        "carga_horaria": carga,
        "nota_minima": nota,
        "obrigatorio": 1 if dados.get("obrigatorio") else 0,
        "setor": setor,
        "status": status,
        "data_inicio": inicio.isoformat() if inicio else None,
        "data_fim": fim.isoformat() if fim else None,
    }
    return limpo, erros


def codigo_existe(db, codigo: str) -> bool:
    return db.execute("SELECT 1 FROM curso WHERE codigo = ?", (codigo,)).fetchone() is not None


def criar_curso(db, curso: dict) -> int:
    """Grava o curso e o modelo de atividades/questões. Quem chama faz o commit."""
    cursor = db.execute(
        "INSERT INTO curso (codigo, titulo, carga_horaria, nota_minima, obrigatorio, setor, "
        "status, data_inicio, data_fim) VALUES (:codigo, :titulo, :carga_horaria, :nota_minima, "
        ":obrigatorio, :setor, :status, :data_inicio, :data_fim)",
        curso,
    )
    adicionar_modelo_ao_curso(db, cursor.lastrowid)
    return cursor.lastrowid
