import sqlite3
import os

DB_NAME = "voz_civica.db"
SQL_FILE = "database_setup.sql"

def init_db():
    # Verifica se o arquivo SQL existe
    if not os.path.exists(SQL_FILE):
        print(f"Erro: Arquivo {SQL_FILE} não encontrado.")
        return

    # Conecta (cria o arquivo se não existir)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    print(f"Criando tabelas em {DB_NAME}...")
    
    with open(SQL_FILE, 'r', encoding='utf-8') as f:
        sql_script = f.read()
        cursor.executescript(sql_script)
    
    conn.commit()
    conn.close()
    print("Banco de dados inicializado com sucesso!")

if __name__ == "__main__":
    init_db()