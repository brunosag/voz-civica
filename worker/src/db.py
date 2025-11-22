import logging
import sqlite3
from pathlib import Path

SCHEMA_FILE = Path('schema.sql')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger(__name__)


def init_db(db_path: Path) -> None:
    if not SCHEMA_FILE.exists():
        logger.error('Erro: Arquivo %s não encontrado.', SCHEMA_FILE)
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    logger.info('Criando tabelas em %s...', db_path)

    with SCHEMA_FILE.open(encoding='utf-8') as f:
        sql_script = f.read()
        cursor.executescript(sql_script)

    conn.commit()
    conn.close()
    logger.info('Banco de dados inicializado com sucesso!')
