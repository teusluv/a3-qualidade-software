"""Emissão, PDF e consulta pública de certificados (RF-07, RF-08, RN-02, RN-03).

A emissão valida tudo NO SERVIDOR e acontece em uma única transação (BEGIN IMMEDIATE), com
`UNIQUE(codigo)` e `UNIQUE(usuario_id, curso_id)` no banco. Pedidos repetidos ou
simultâneos devolvem o mesmo certificado (A-07).
"""

import io
import re
import secrets
import sqlite3
from datetime import datetime

from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

from app.config import CODIGO_CERTIFICADO_BYTES
from app.services import avaliacao
from app.services.logs import agora, registrar

TENTATIVAS_DE_CODIGO = 5
PARTICULAS = {"da", "de", "do", "das", "dos", "e"}
PADRAO_CODIGO = re.compile(r"^[A-Za-z0-9_-]{8,64}$")


class ErroEmissao(Exception):
    """A emissão foi negada; a mensagem pode ser mostrada ao usuário."""


def gerar_codigo() -> str:
    """Código imprevisível (nunca sequencial)."""
    return secrets.token_urlsafe(CODIGO_CERTIFICADO_BYTES)


def codigo_tem_formato_valido(codigo: str) -> bool:
    return bool(PADRAO_CODIGO.match(codigo))


def mascarar_nome(nome: str) -> str:
    """'Carla Mendes Lima' -> 'Carla M. L.' (A-05). Preposições são descartadas."""
    partes = nome.split()
    if len(partes) <= 1:
        return " ".join(partes)
    iniciais = [f"{p[0].upper()}." for p in partes[1:] if p.lower() not in PARTICULAS]
    return " ".join([partes[0], *iniciais])


def formatar_data(iso: str) -> str:
    """'2026-11-16T10:30:00' -> '16/11/2026'."""
    return datetime.fromisoformat(iso).strftime("%d/%m/%Y")


def _dados_de_elegibilidade(db, usuario_id: int, curso_id: int):
    curso = db.execute("SELECT * FROM curso WHERE id = ?", (curso_id,)).fetchone()
    inscricao = db.execute(
        "SELECT id FROM inscricao WHERE usuario_id = ? AND curso_id = ?", (usuario_id, curso_id)
    ).fetchone()
    return curso, inscricao


def emitir_certificado(db, usuario_id: int, curso_id: int):
    """Devolve (certificado, criado_agora). Levanta ErroEmissao se não for elegível."""
    if not db.in_transaction:
        db.execute("BEGIN IMMEDIATE")  # serializa emissões simultâneas
    try:
        existente = db.execute(
            "SELECT * FROM certificado WHERE usuario_id = ? AND curso_id = ?",
            (usuario_id, curso_id),
        ).fetchone()
        if existente:
            db.commit()
            return existente, False

        curso, inscricao = _dados_de_elegibilidade(db, usuario_id, curso_id)
        if curso is None or inscricao is None:
            raise ErroEmissao("Você ainda não iniciou este curso.")

        total = db.execute(
            "SELECT COUNT(*) FROM atividade WHERE curso_id = ?", (curso_id,)
        ).fetchone()[0]
        concluidas = db.execute(
            "SELECT COUNT(*) FROM progresso WHERE inscricao_id = ?", (inscricao["id"],)
        ).fetchone()[0]
        notas = [
            linha["nota"]
            for linha in db.execute(
                "SELECT nota FROM tentativa WHERE inscricao_id = ?", (inscricao["id"],)
            )
        ]
        if not avaliacao.atividades_concluidas(concluidas, total):
            raise ErroEmissao("Conclua todas as atividades do curso para emitir o certificado.")
        if not avaliacao.elegivel_para_certificado(
            avaliacao.maior_nota(notas), curso["nota_minima"], True
        ):
            raise ErroEmissao("É necessário ser aprovado na avaliação para emitir o certificado.")

        minimo = avaliacao.nota_minima_efetiva(curso["nota_minima"])
        concluido_em = db.execute(
            "SELECT MIN(realizada_em) FROM tentativa WHERE inscricao_id = ? AND nota >= ?",
            (inscricao["id"], minimo),
        ).fetchone()[0]

        certificado = None
        for _ in range(TENTATIVAS_DE_CODIGO):
            try:
                db.execute(
                    "INSERT INTO certificado (usuario_id, curso_id, codigo, concluido_em, "
                    "emitido_em) VALUES (?, ?, ?, ?, ?)",
                    (usuario_id, curso_id, gerar_codigo(), concluido_em, agora()),
                )
            except sqlite3.IntegrityError:
                continue  # colisão de código (praticamente impossível): sorteia outro
            certificado = db.execute(
                "SELECT * FROM certificado WHERE usuario_id = ? AND curso_id = ?",
                (usuario_id, curso_id),
            ).fetchone()
            break
        if certificado is None:
            raise RuntimeError("Não foi possível gerar um código único.")

        registrar(db, "certificado_emitido", usuario_id, f"certificado={certificado['id']}")
        db.commit()
        return certificado, True
    except BaseException:
        db.rollback()
        raise


def obter_certificado_para_pdf(db, certificado_id: int):
    return db.execute(
        "SELECT ce.id, ce.usuario_id, ce.codigo, ce.concluido_em, "
        "       u.nome, u.matricula, c.titulo, c.carga_horaria "
        "FROM certificado ce "
        "JOIN usuario u ON u.id = ce.usuario_id "
        "JOIN curso c ON c.id = ce.curso_id "
        "WHERE ce.id = ?",
        (certificado_id,),
    ).fetchone()


def gerar_pdf(dados) -> bytes:
    """Gera o PDF do certificado (CA-07: nenhum campo vazio)."""
    campos = {
        "nome": dados["nome"],
        "matricula": dados["matricula"],
        "curso": dados["titulo"],
        "carga horária": f"{dados['carga_horaria']} horas",
        "data de conclusão": formatar_data(dados["concluido_em"]),
        "código": dados["codigo"],
    }
    if any(not str(valor).strip() for valor in campos.values()):
        raise ValueError("Certificado com campo vazio.")

    buffer = io.BytesIO()
    largura, altura = landscape(A4)
    pdf = canvas.Canvas(buffer, pagesize=landscape(A4))
    pdf.setTitle("Certificado de Conclusão")

    pdf.setFont("Helvetica-Bold", 30)
    pdf.drawCentredString(largura / 2, altura - 90, "Certificado de Conclusão")
    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(largura / 2, altura - 125, "Hospital da Mulher · Educação Permanente")

    pdf.setFont("Helvetica", 16)
    pdf.drawCentredString(largura / 2, altura - 185, "Certificamos que")
    pdf.setFont("Helvetica-Bold", 24)
    pdf.drawCentredString(largura / 2, altura - 220, campos["nome"])
    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(largura / 2, altura - 248, f"Matrícula {campos['matricula']}")

    pdf.setFont("Helvetica", 16)
    pdf.drawCentredString(largura / 2, altura - 295, "concluiu com aproveitamento o curso")
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawCentredString(largura / 2, altura - 325, campos["curso"])
    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(
        largura / 2,
        altura - 355,
        f"Carga horária: {campos['carga horária']} · Concluído em {campos['data de conclusão']}",
    )

    pdf.line(largura / 2 - 120, 120, largura / 2 + 120, 120)
    pdf.setFont("Helvetica", 11)
    pdf.drawCentredString(largura / 2, 104, "Coordenação de Educação Permanente")
    pdf.drawCentredString(largura / 2, 90, "(assinatura ilustrativa · dados fictícios)")

    pdf.setFont("Helvetica", 10)
    pdf.drawCentredString(largura / 2, 50, f"Código de autenticidade: {campos['código']}")
    pdf.drawCentredString(largura / 2, 36, "Verifique em /verificar informando o código acima.")
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def consultar_publico(db, codigo: str):
    """Consulta pública: devolve só o mínimo necessário (A-05, CA-12)."""
    linha = db.execute(
        "SELECT ce.codigo, ce.concluido_em, u.nome, c.titulo, c.carga_horaria "
        "FROM certificado ce "
        "JOIN usuario u ON u.id = ce.usuario_id "
        "JOIN curso c ON c.id = ce.curso_id "
        "WHERE ce.codigo = ?",
        (codigo,),
    ).fetchone()
    if linha is None:
        return None
    return {
        "codigo": linha["codigo"],
        "curso": linha["titulo"],
        "carga_horaria": linha["carga_horaria"],
        "concluido_em": formatar_data(linha["concluido_em"]),
        "nome_mascarado": mascarar_nome(linha["nome"]),
    }
