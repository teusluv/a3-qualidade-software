"""Conteúdo do curso editado pelo administrador: atividades, questões e links de vídeo.

As funções `validar_*` são puras. As demais recebem `db` e NÃO fazem commit (quem chama decide).
"""

from collections.abc import Mapping
from urllib.parse import urlparse

from app.services.logs import agora

LETRAS = ("a", "b", "c", "d")


class ConteudoInvalidoError(Exception):
    """A operação foi recusada; a mensagem pode ser mostrada ao usuário."""


# ---------- validações (puras) ----------


def validar_titulo_atividade(titulo) -> tuple[str, list[str]]:
    limpo = (titulo or "").strip()
    erros = []
    if not 3 <= len(limpo) <= 100:
        erros.append("Atividade: informe um título de 3 a 100 caracteres.")
    return limpo, erros


def validar_link(titulo, url) -> tuple[dict, list[str]]:
    """Aceita só endereços http ou https (nada de javascript:, data: ou arquivos locais)."""
    erros: list[str] = []
    titulo = (titulo or "").strip()
    url = (url or "").strip()
    if not 3 <= len(titulo) <= 100:
        erros.append("Link: informe um título de 3 a 100 caracteres.")
    partes = urlparse(url)
    endereco_ok = (
        partes.scheme in ("http", "https")
        and bool(partes.netloc)
        and len(url) <= 500
        and not any(c.isspace() or ord(c) < 32 for c in url)
    )
    if not endereco_ok:
        erros.append("Link: informe um endereço completo que comece com http:// ou https://.")
    return {"titulo": titulo, "url": url}, erros


def validar_questao(dados: Mapping) -> tuple[dict, list[str]]:
    erros: list[str] = []
    enunciado = (dados.get("enunciado") or "").strip()
    if not 5 <= len(enunciado) <= 300:
        erros.append("Pergunta: informe de 5 a 300 caracteres.")

    opcoes = {}
    for letra in LETRAS:
        texto = (dados.get(f"opcao_{letra}") or "").strip()
        if not 1 <= len(texto) <= 150:
            erros.append(f"Resposta {letra.upper()}: informe de 1 a 150 caracteres.")
        opcoes[letra] = texto
    textos = [t.lower() for t in opcoes.values() if t]
    if len(set(textos)) != len(textos):
        erros.append("Respostas: as quatro opções precisam ser diferentes entre si.")

    correta = (dados.get("correta") or "").strip().lower()
    if correta not in LETRAS:
        erros.append("Resposta certa: escolha uma das letras A, B, C ou D.")

    limpo = {"enunciado": enunciado, "correta": correta}
    limpo.update({f"opcao_{letra}": texto for letra, texto in opcoes.items()})
    return limpo, erros


# ---------- atividades ----------


def listar_atividades_admin(db, curso_id: int):
    return db.execute(
        "SELECT a.id, a.ordem, a.titulo, "
        "       (SELECT COUNT(*) FROM progresso p WHERE p.atividade_id = a.id) AS conclusoes "
        "FROM atividade a WHERE a.curso_id = ? ORDER BY a.ordem",
        (curso_id,),
    ).fetchall()


def criar_atividade(db, curso_id: int, titulo: str) -> None:
    db.execute(
        "INSERT INTO atividade (curso_id, ordem, titulo) VALUES (?, "
        "(SELECT COALESCE(MAX(ordem), 0) + 1 FROM atividade WHERE curso_id = ?), ?)",
        (curso_id, curso_id, titulo),
    )


def obter_atividade(db, atividade_id: int):
    return db.execute("SELECT * FROM atividade WHERE id = ?", (atividade_id,)).fetchone()


def renomear_atividade(db, atividade_id: int, titulo: str) -> None:
    db.execute("UPDATE atividade SET titulo = ? WHERE id = ?", (titulo, atividade_id))


def remover_atividade(db, atividade_id: int) -> None:
    """Só remove se ninguém concluiu a atividade: o histórico de progresso não pode ser perdido."""
    concluidas = db.execute(
        "SELECT COUNT(*) FROM progresso WHERE atividade_id = ?", (atividade_id,)
    ).fetchone()[0]
    if concluidas:
        raise ConteudoInvalidoError(
            f"Esta atividade já foi concluída por {concluidas} pessoa(s) e não pode ser removida. "
            "Renomeie-a em vez disso."
        )
    db.execute("DELETE FROM atividade WHERE id = ?", (atividade_id,))


# ---------- questões ----------


def listar_questoes_admin(db, curso_id: int):
    return db.execute(
        "SELECT id, ordem, enunciado, opcao_a, opcao_b, opcao_c, opcao_d, correta "
        "FROM questao WHERE curso_id = ? ORDER BY ordem",
        (curso_id,),
    ).fetchall()


def obter_questao(db, questao_id: int):
    return db.execute("SELECT * FROM questao WHERE id = ?", (questao_id,)).fetchone()


def criar_questao(db, curso_id: int, q: dict) -> None:
    db.execute(
        "INSERT INTO questao (curso_id, ordem, enunciado, opcao_a, opcao_b, opcao_c, opcao_d, "
        "correta) VALUES (?, (SELECT COALESCE(MAX(ordem), 0) + 1 FROM questao WHERE curso_id = ?), "
        "?, ?, ?, ?, ?, ?)",
        (curso_id, curso_id, q["enunciado"], q["opcao_a"], q["opcao_b"], q["opcao_c"],
         q["opcao_d"], q["correta"]),
    )


def atualizar_questao(db, questao_id: int, q: dict) -> None:
    db.execute(
        "UPDATE questao SET enunciado = ?, opcao_a = ?, opcao_b = ?, opcao_c = ?, opcao_d = ?, "
        "correta = ? WHERE id = ?",
        (q["enunciado"], q["opcao_a"], q["opcao_b"], q["opcao_c"], q["opcao_d"], q["correta"],
         questao_id),
    )


def remover_questao(db, questao_id: int) -> None:
    db.execute("DELETE FROM questao WHERE id = ?", (questao_id,))


# ---------- links de vídeo ----------


def listar_links(db, curso_id: int):
    return db.execute(
        "SELECT id, titulo, url FROM link_curso WHERE curso_id = ? ORDER BY id", (curso_id,)
    ).fetchall()


def criar_link(db, curso_id: int, link: dict) -> None:
    db.execute(
        "INSERT INTO link_curso (curso_id, titulo, url, criado_em) VALUES (?, ?, ?, ?)",
        (curso_id, link["titulo"], link["url"], agora()),
    )


def obter_link(db, link_id: int):
    return db.execute("SELECT * FROM link_curso WHERE id = ?", (link_id,)).fetchone()


def remover_link(db, link_id: int) -> None:
    db.execute("DELETE FROM link_curso WHERE id = ?", (link_id,))
