"""Configuração central do portal.

Regras de negócio configuráveis ficam aqui, em um só lugar, para que uma mudança de
política (hipóteses A-02, A-06 e outras) não exija mexer na lógica.
"""

import os
import secrets
from datetime import timedelta

# --- Regras de negócio (hipóteses de trabalho do README) ---
NOTA_MINIMA_PADRAO = 70  # RN-01: um curso pode exigir mais, nunca menos
MAX_TENTATIVAS = 3  # A-02 / A-07: total por colaborador e curso
PERCENTUAL_ATIVIDADES_PARA_AVALIAR = 100  # A-06
QUESTOES_POR_AVALIACAO = 10
CODIGO_CERTIFICADO_BYTES = 16  # RN-03: secrets.token_urlsafe(16)

# --- Material dos cursos (upload) ---
TAMANHO_MAXIMO_UPLOAD = 20 * 1024 * 1024  # 20 MB
EXTENSOES_PERMITIDAS = ("pdf", "docx", "pptx", "txt", "png", "jpg", "jpeg")

# --- Sessão ---
SESSAO_MINUTOS = 30
TAMANHO_MAXIMO_CAMPO_LOGIN = 64
# Proteção contra força bruta no login
MAX_FALHAS_POR_MATRICULA = 3
MAX_FALHAS_POR_ORIGEM = 10

class Config:
    # Sem chave fixa no código: se SECRET_KEY não estiver definida, gera uma por execução
    # (as sessões deixam de valer ao reiniciar o servidor, o que é aceitável no protótipo).
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

    MAX_CONTENT_LENGTH = TAMANHO_MAXIMO_UPLOAD  # o Flask recusa (413) corpos maiores que isso

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Em HTTPS, defina SESSION_COOKIE_SECURE=1. No protótipo local (HTTP) fica desligado.
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE") == "1"
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=SESSAO_MINUTOS)
