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

# --- Sessão ---
SESSAO_MINUTOS = 30
TAMANHO_MAXIMO_CAMPO_LOGIN = 64

# --- Proteção do login contra força bruta (defeito D-02) ---
# Contagem por (endereço de origem, matrícula) e também só por endereço, para que uma
# varredura de várias matrículas a partir do mesmo lugar também seja contida.
MAX_FALHAS_POR_MATRICULA = 5
MAX_FALHAS_POR_ORIGEM = 15
JANELA_FALHAS_MINUTOS = 10
BLOQUEIO_MINUTOS = 5

# --- Cabeçalhos de segurança (defeito D-03) ---
# O Bootstrap vem de CDN, por isso o domínio aparece em style-src e script-src.
# 'unsafe-inline' em style-src é necessário porque as barras de progresso usam style="width: X%".
# Não há script embutido em nenhuma página, então script-src fica sem 'unsafe-inline'.
CSP = (
    "default-src 'self'; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "script-src 'self' https://cdn.jsdelivr.net; "
    "img-src 'self' data:; "
    "font-src 'self' https://cdn.jsdelivr.net; "
    "connect-src 'self'; "
    "form-action 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "object-src 'none'"
)
CABECALHOS_SEGURANCA = {
    "Content-Security-Policy": CSP,
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    # no-referrer também impede que o código do certificado (que vai na URL da
    # verificação) saia no cabeçalho Referer para terceiros: ver defeito D-01.
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}
# D-04 (versão do servidor no cabeçalho Server) NÃO se resolve aqui: quem emite esse
# cabeçalho é o servidor de desenvolvimento do Flask, antes da aplicação. Definir "Server"
# nesta lista só faz o cabeçalho aparecer duas vezes. A correção é de implantação: usar um
# servidor WSGI real (gunicorn, waitress) atrás de um proxy que remova o cabeçalho.


class Config:
    # Sem chave fixa no código: se SECRET_KEY não estiver definida, gera uma por execução
    # (as sessões deixam de valer ao reiniciar o servidor, o que é aceitável no protótipo).
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Em HTTPS, defina SESSION_COOKIE_SECURE=1. No protótipo local (HTTP) fica desligado.
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE") == "1"
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=SESSAO_MINUTOS)
