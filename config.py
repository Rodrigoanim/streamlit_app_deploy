# Programa: config.py
# Data: 18/02/2025
# Hora: 17:40cd


import os
from pathlib import Path

# Verifica se está em ambiente de produção (Render.com)
IS_PRODUCTION = os.getenv('RENDER') == 'true'

# Define o caminho base dependendo do ambiente
if IS_PRODUCTION:
    DATA_DIR = Path('/var/data')
else:
    # Caminho local para desenvolvimento
    DATA_DIR = Path(__file__).parent / 'data'

# Cria o diretório de dados se não existir
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Caminho do banco de dados
DB_PATH = DATA_DIR / 'calcpc.db'
