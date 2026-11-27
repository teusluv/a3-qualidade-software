"""Cadastro de cursos pelo administrador (RF-09).

`validar_curso` é uma função pura (fácil de testar). Todo curso novo recebe as 4 atividades e as
10 questões-modelo do `seed_data`: não há tela para editar questões neste protótipo.
"""

import re
from collections.abc import Mapping
from datetime import date
from pathlib import Path

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


def validar_curso(
    dados: Mapping, setores_validos: set[str], status_permitidos: tuple[str, ...] = STATUS_NOVO
) -> tuple[dict, list[str]]:
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
    if status not in status_permitidos:
        erros.append(f"Situação: escolha {' ou '.join(status_permitidos)}.")

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


def codigo_existe(db, codigo: str, ignorar_id: int | None = None) -> bool:
    """Já existe outro curso com este código? (`ignorar_id` é o próprio curso, na edição)."""
    return (
        db.execute(
            "SELECT 1 FROM curso WHERE codigo = ? AND id IS NOT ?", (codigo, ignorar_id)
        ).fetchone()
        is not None
    )


def listar_codigos(db) -> list[str]:
    return [linha["codigo"] for linha in db.execute("SELECT codigo FROM curso ORDER BY codigo")]


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


def atualizar_curso(db, curso_id: int, curso: dict) -> None:
    """Grava as alterações dos dados do curso. Quem chama faz o commit."""
    db.execute(
        "UPDATE curso SET codigo = :codigo, titulo = :titulo, carga_horaria = :carga_horaria, "
        "nota_minima = :nota_minima, obrigatorio = :obrigatorio, setor = :setor, "
        "status = :status, data_inicio = :data_inicio, data_fim = :data_fim WHERE id = :id",
        {**curso, "id": curso_id},
    )


class CursoComHistoricoError(Exception):
    """O curso tem inscrições ou certificados e não pode ser excluído (RN-05)."""


def curso_tem_historico(db, curso_id: int) -> bool:
    inscricoes = db.execute("SELECT COUNT(*) FROM inscricao WHERE curso_id = ?", (curso_id,))
    certificados = db.execute("SELECT COUNT(*) FROM certificado WHERE curso_id = ?", (curso_id,))
    return (inscricoes.fetchone()[0] + certificados.fetchone()[0]) > 0


def excluir_curso(db, pasta_uploads: str, curso_id: int) -> None:
    """Exclui o curso e o que é só dele; recusa se houver histórico. Quem chama faz o commit."""
    if curso_tem_historico(db, curso_id):
        raise CursoComHistoricoError(
            "Este curso tem histórico de colaboradores e não pode ser excluído. "
            "Arquive-o: ele deixa de aparecer no catálogo e o histórico é preservado."
        )
    arquivos = [
        linha["arquivo"]
        for linha in db.execute("SELECT arquivo FROM material WHERE curso_id = ?", (curso_id,))
    ]
    db.execute("DELETE FROM material WHERE curso_id = ?", (curso_id,))
    db.execute("DELETE FROM link_curso WHERE curso_id = ?", (curso_id,))
    db.execute("DELETE FROM questao WHERE curso_id = ?", (curso_id,))
    db.execute("DELETE FROM atividade WHERE curso_id = ?", (curso_id,))
    db.execute("DELETE FROM curso WHERE id = ?", (curso_id,))
    for arquivo in arquivos:  # só apaga do disco depois de o banco aceitar tudo
        (Path(pasta_uploads) / arquivo).unlink(missing_ok=True)
