"""Envios simultâneos da avaliação não podem ultrapassar o limite de tentativas (A-02/A-07)."""

import sqlite3
from concurrent.futures import ThreadPoolExecutor

from app.config import MAX_TENTATIVAS
from app.services import cursos


def test_oito_envios_simultaneos_gravam_no_maximo_o_limite(
    caminho_banco, aprovar_por_sql, consulta
):
    inscricao = aprovar_por_sql("1001", "A", nota=60)  # já tem 1 tentativa gravada

    def enviar(_):
        conexao = sqlite3.connect(caminho_banco, timeout=30)
        conexao.row_factory = sqlite3.Row
        try:
            gravada = cursos.registrar_tentativa_se_permitida(
                conexao, inscricao, 5, 10, 50, MAX_TENTATIVAS
            )
            if gravada is not None:
                conexao.commit()
            return gravada
        finally:
            conexao.close()

    with ThreadPoolExecutor(max_workers=8) as pool:
        resultados = list(pool.map(enviar, range(8)))

    total = consulta("SELECT COUNT(*) AS n FROM tentativa WHERE inscricao_id = ?", (inscricao,))
    assert total[0]["n"] == MAX_TENTATIVAS
    assert sum(1 for r in resultados if r is not None) == MAX_TENTATIVAS - 1
