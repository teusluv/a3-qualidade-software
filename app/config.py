
"""Configuração central do portal.

Regras de negócio configuráveis ficam aqui, em um só lugar.
"""

import os
import secrets
from datetime import timedelta

# --- Regras de negócio ---
NOTA_MINIMA_PADRAO = 70
MAX_TENTATIVAS = 3
PERCENTUAL_ATIVIDADES_PARA_AVALIAR = 100
QUESTOES_POR_AVALIACAO = 10
CODIGO_CERTIFICADO_BYTES = 16

# --- Proteção contra força bruta no login ---
MAX_FALHAS_POR_MATRICULA = 3
MAX_FALHAS_POR_ORIGEM = 10

# --- Material dos cursos (upload) ---
TAMANHO_MAXIMO_UPLOAD = 20 * 1024 * 1024
EXTENSOES_PERMITIDAS = ("pdf", "docx", "pptx", "txt", "png", "jpg", "jpeg")

# --- Sessão ---
SESSAO_MINUTOS = 30
TAMANHO_MAXIMO_CAMPO_LOGIN = 64


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

    MAX_CONTENT_LENGTH = TAMANHO_MAXIMO_UPLOAD

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE") == "1"
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=SESSAO_MINUTOS)
