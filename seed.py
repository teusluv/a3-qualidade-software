"""Cria o banco do protótipo e carrega os dados fictícios.

Uso: python seed.py   (pode ser repetido sem duplicar dados)
"""

from app import create_app
from app.db import get_db, init_db
from app.seed_data import carregar_dados

if __name__ == "__main__":
    app = create_app({"AVISAR_BANCO_VAZIO": False})  # o seed é quem cria os dados
    with app.app_context():
        init_db()
        carregar_dados(get_db())
    print(f"Banco pronto em {app.config['DATABASE']}")
