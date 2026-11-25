"""Material de estudo anexado aos cursos (upload feito pelo administrador).

Segurança: só extensões permitidas; confere a assinatura (primeiros bytes) do arquivo; o nome
no disco é gerado (o nome enviado nunca vira caminho); o download sai como anexo.
"""

from pathlib import Path
from uuid import uuid4

from werkzeug.utils import secure_filename

from app.config import EXTENSOES_PERMITIDAS
from app.services.logs import agora

ASSINATURAS = {
    "pdf": (b"%PDF",),
    "docx": (b"PK\x03\x04",),
    "pptx": (b"PK\x03\x04",),
    "png": (b"\x89PNG",),
    "jpg": (b"\xff\xd8\xff",),
    "jpeg": (b"\xff\xd8\xff",),
}


class MaterialInvalidoError(Exception):
    """O arquivo foi recusado; a mensagem pode ser mostrada ao usuário."""


def extensao_de(nome: str) -> str:
    return nome.rsplit(".", 1)[-1].lower() if "." in nome else ""


def extensao_permitida(nome: str) -> bool:
    return extensao_de(nome) in EXTENSOES_PERMITIDAS


def assinatura_valida(extensao: str, cabecalho: bytes) -> bool:
    """PDF, Office, PNG e JPEG precisam começar com a assinatura certa; TXT precisa ser texto."""
    if extensao == "txt":
        try:
            cabecalho.decode("utf-8")
        except UnicodeDecodeError:
            return False
        return b"\x00" not in cabecalho
    return any(cabecalho.startswith(a) for a in ASSINATURAS.get(extensao, ()))


def salvar_material(db, pasta: str, curso_id: int, arquivo, usuario_id: int) -> int:
    """Valida, grava no disco e registra no banco. Quem chama faz o commit."""
    if arquivo is None or not arquivo.filename:
        raise MaterialInvalidoError("Escolha um arquivo para enviar.")
    nome_original = secure_filename(arquivo.filename)
    if not nome_original or not extensao_permitida(nome_original):
        permitidas = ", ".join(EXTENSOES_PERMITIDAS)
        raise MaterialInvalidoError(f"Tipo de arquivo não permitido. Use: {permitidas}.")

    extensao = extensao_de(nome_original)
    cabecalho = arquivo.stream.read(1024)
    arquivo.stream.seek(0)
    if not cabecalho or not assinatura_valida(extensao, cabecalho):
        raise MaterialInvalidoError("O conteúdo do arquivo não corresponde ao tipo informado.")

    Path(pasta).mkdir(parents=True, exist_ok=True)
    nome_no_disco = f"{uuid4().hex}.{extensao}"
    destino = Path(pasta) / nome_no_disco
    arquivo.save(destino)
    try:
        cursor = db.execute(
            "INSERT INTO material (curso_id, nome_original, arquivo, tamanho, enviado_por, "
            "enviado_em) VALUES (?, ?, ?, ?, ?, ?)",
            (curso_id, nome_original, nome_no_disco, destino.stat().st_size, usuario_id, agora()),
        )
    except BaseException:
        destino.unlink(missing_ok=True)
        raise
    return cursor.lastrowid


def listar_materiais(db, curso_id: int):
    return db.execute(
        "SELECT id, nome_original, tamanho, enviado_em FROM material "
        "WHERE curso_id = ? ORDER BY id",
        (curso_id,),
    ).fetchall()


def obter_material(db, material_id: int, curso_id: int):
    return db.execute(
        "SELECT * FROM material WHERE id = ? AND curso_id = ?", (material_id, curso_id)
    ).fetchone()


def remover_material(db, pasta: str, material_id: int) -> bool:
    """Apaga o registro e o arquivo. Quem chama faz o commit."""
    material = db.execute("SELECT arquivo FROM material WHERE id = ?", (material_id,)).fetchone()
    if material is None:
        return False
    db.execute("DELETE FROM material WHERE id = ?", (material_id,))
    (Path(pasta) / material["arquivo"]).unlink(missing_ok=True)
    return True
