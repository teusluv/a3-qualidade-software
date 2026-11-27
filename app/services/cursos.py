"""Consultas e regras de cursos, inscrição, atividades e tentativas (RF-02 a RF-06, RF-10).

Recebem a conexão `db` como parâmetro, sem depender do Flask. As funções que gravam NÃO
fazem commit: quem chama decide, para poder gravar o log na mesma transação.
"""

from datetime import date

from app.services import avaliacao
from app.services.logs import agora

# Resumo de um curso para um usuário: progresso, melhor nota, tentativas e certificado.
_RESUMO = """
SELECT c.*,
       i.id AS inscricao_id,
       (SELECT COUNT(*) FROM atividade a WHERE a.curso_id = c.id) AS total_atividades,
       (SELECT COUNT(*) FROM progresso p WHERE p.inscricao_id = i.id) AS concluidas,
       (SELECT MAX(t.nota) FROM tentativa t WHERE t.inscricao_id = i.id) AS melhor_nota,
       (SELECT COUNT(*) FROM tentativa t WHERE t.inscricao_id = i.id) AS tentativas,
       (SELECT ce.id FROM certificado ce
         WHERE ce.usuario_id = :uid AND ce.curso_id = c.id) AS certificado_id
  FROM curso c
  LEFT JOIN inscricao i ON i.curso_id = c.id AND i.usuario_id = :uid
"""


def curso_aceita_novo_inicio(status: str, data_inicio: str, data_fim: str, hoje: date) -> bool:
    """CA-03: só curso ativo e dentro do período aceita NOVO início (A-08)."""
    return status == "ativo" and data_inicio <= hoje.isoformat() <= data_fim


def listar_catalogo(db, usuario_id: int, setor: str):
    """RF-02 / RN-04: cursos aplicáveis ao setor; arquivados ficam fora do catálogo."""
    return db.execute(
        _RESUMO
        + " WHERE c.status != 'arquivado' AND (c.setor IS NULL OR c.setor = :setor)"
        + " ORDER BY c.obrigatorio DESC, c.titulo",
        {"uid": usuario_id, "setor": setor},
    ).fetchall()


def listar_historico(db, usuario_id: int):
    """RF-10 / RN-05: tudo o que o colaborador iniciou, inclusive cursos arquivados."""
    return db.execute(
        _RESUMO + " WHERE i.id IS NOT NULL ORDER BY i.iniciado_em DESC",
        {"uid": usuario_id},
    ).fetchall()


def obter_resumo(db, usuario_id: int, curso_id: int):
    return db.execute(
        _RESUMO + " WHERE c.id = :cid", {"uid": usuario_id, "cid": curso_id}
    ).fetchone()


def iniciar_curso(db, usuario_id: int, curso_id: int) -> int:
    db.execute(
        "INSERT OR IGNORE INTO inscricao (usuario_id, curso_id, iniciado_em) VALUES (?, ?, ?)",
        (usuario_id, curso_id, agora()),
    )
    return db.execute(
        "SELECT id FROM inscricao WHERE usuario_id = ? AND curso_id = ?", (usuario_id, curso_id)
    ).fetchone()["id"]


def listar_atividades(db, curso_id: int, inscricao_id: int | None):
    return db.execute(
        "SELECT a.id, a.ordem, a.titulo, p.concluida_em "
        "FROM atividade a LEFT JOIN progresso p "
        "  ON p.atividade_id = a.id AND p.inscricao_id = ? "
        "WHERE a.curso_id = ? ORDER BY a.ordem",
        (inscricao_id, curso_id),
    ).fetchall()


def concluir_atividade(db, inscricao_id: int, curso_id: int, atividade_id: int) -> bool:
    """Marca a atividade como concluída. Falso se ela não pertence ao curso."""
    pertence = db.execute(
        "SELECT 1 FROM atividade WHERE id = ? AND curso_id = ?", (atividade_id, curso_id)
    ).fetchone()
    if pertence is None:
        return False
    db.execute(
        "INSERT OR IGNORE INTO progresso (inscricao_id, atividade_id, concluida_em) "
        "VALUES (?, ?, ?)",
        (inscricao_id, atividade_id, agora()),
    )
    return True


def listar_questoes(db, curso_id: int):
    """Questões SEM o gabarito: a resposta certa nunca vai para o navegador."""
    return db.execute(
        "SELECT id, ordem, enunciado, opcao_a, opcao_b, opcao_c, opcao_d "
        "FROM questao WHERE curso_id = ? ORDER BY ordem",
        (curso_id,),
    ).fetchall()


def obter_gabarito(db, curso_id: int) -> dict[int, str]:
    linhas = db.execute("SELECT id, correta FROM questao WHERE curso_id = ?", (curso_id,))
    return {linha["id"]: linha["correta"] for linha in linhas}


def registrar_tentativa_se_permitida(
    db, inscricao_id: int, acertos: int, total: int, nota: int, maximo: int
) -> int | None:
    """Grava a tentativa só se o limite ainda não foi atingido, de forma atômica.

    A contagem e a gravação ocorrem na mesma transação (BEGIN IMMEDIATE), então dois envios
    simultâneos não conseguem ultrapassar o limite. Devolve o id da tentativa, ou None se o
    limite já foi atingido. Quem chama faz o commit (junto com o log).
    """
    if not db.in_transaction:
        db.execute("BEGIN IMMEDIATE")
    try:
        feitas = db.execute(
            "SELECT COUNT(*) FROM tentativa WHERE inscricao_id = ?", (inscricao_id,)
        ).fetchone()[0]
        if not avaliacao.pode_tentar(feitas, maximo):
            db.rollback()
            return None
        cursor = db.execute(
            "INSERT INTO tentativa (inscricao_id, acertos, total, nota, realizada_em) "
            "VALUES (?, ?, ?, ?, ?)",
            (inscricao_id, acertos, total, nota, agora()),
        )
        return cursor.lastrowid
    except BaseException:
        db.rollback()
        raise


def obter_tentativa(db, tentativa_id: int, usuario_id: int, curso_id: int):
    """Só devolve a tentativa se ela for do usuário e do curso informados."""
    return db.execute(
        "SELECT t.* FROM tentativa t JOIN inscricao i ON i.id = t.inscricao_id "
        "WHERE t.id = ? AND i.usuario_id = ? AND i.curso_id = ?",
        (tentativa_id, usuario_id, curso_id),
    ).fetchone()


def listar_concluintes(db, curso_id: int):
    """Quem concluiu o curso (tem certificado): para o administrador consultar o histórico."""
    return db.execute(
        "SELECT u.nome, u.matricula, u.setor, ce.concluido_em, ce.codigo, "
        "       (SELECT MAX(t.nota) FROM tentativa t JOIN inscricao i ON i.id = t.inscricao_id "
        "         WHERE i.usuario_id = ce.usuario_id AND i.curso_id = ce.curso_id) AS melhor_nota "
        "FROM certificado ce JOIN usuario u ON u.id = ce.usuario_id "
        "WHERE ce.curso_id = ? ORDER BY ce.concluido_em DESC",
        (curso_id,),
    ).fetchall()
