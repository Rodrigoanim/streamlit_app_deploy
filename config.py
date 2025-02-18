# Programa: config.py
# Data: 18/02/2025
# Hora: 13H00


import os
from pathlib import Path

# Detecta se está rodando em produção ou desenvolvimento
IS_PRODUCTION = os.getenv('STREAMLIT_SERVER_PORT') is not None

# Configuração dos caminhos
if IS_PRODUCTION:
    # Caminho para produção (SSD montado)
    DATA_DIR = Path('/var/data')
else:
    # Caminho para desenvolvimento local
    DATA_DIR = Path.cwd() / 'data'

# Cria o diretório de dados se não existir
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Caminho do banco de dados
DB_PATH = DATA_DIR / 'calcpc.db'
