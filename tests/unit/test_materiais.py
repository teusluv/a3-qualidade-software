"""Caixa-branca: regras do upload de material (extensão e assinatura do arquivo)."""

import pytest

from app.services.materiais import assinatura_valida, extensao_de, extensao_permitida


@pytest.mark.parametrize(
    ("nome", "esperado"),
    [
        ("aula.pdf", True), ("AULA.PDF", True), ("slides.pptx", True), ("texto.txt", True),
        ("foto.JPG", True), ("virus.exe", False), ("script.py", False), ("pagina.html", False),
        ("semextensao", False), ("duplo.pdf.exe", False), ("", False),
    ],
)
def test_extensao_permitida(nome, esperado):
    assert extensao_permitida(nome) is esperado


def test_extensao_de():
    assert extensao_de("a.b.PDF") == "pdf"
    assert extensao_de("semponto") == ""


@pytest.mark.parametrize(
    ("extensao", "cabecalho", "esperado"),
    [
        ("pdf", b"%PDF-1.7 ...", True),
        ("pdf", b"MZ\x90\x00 executavel", False),  # .pdf que na verdade é executável
        ("docx", b"PK\x03\x04...", True),
        ("docx", b"%PDF", False),
        ("png", b"\x89PNG\r\n\x1a\n", True),
        ("jpg", b"\xff\xd8\xff\xe0", True),
        ("jpeg", b"\xff\xd8\xff\xe1", True),
        ("txt", "texto com acentuação".encode(), True),
        ("txt", b"\xff\xfe\x00binario", False),
        ("txt", b"com nulo\x00dentro", False),
        ("zip", b"PK\x03\x04", False),  # extensão sem regra
    ],
)
def test_assinatura_valida(extensao, cabecalho, esperado):
    assert assinatura_valida(extensao, cabecalho) is esperado
