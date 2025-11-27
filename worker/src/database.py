from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import pathlib

BASE_DIR = pathlib.Path(__file__).parent.parent
DB_PATH = BASE_DIR / "voz_civica.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Cria a engine
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} # Necessário para SQLite
)

# Cria a fábrica de sessões
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Classe Base para os Models herdarem
class Base(DeclarativeBase):
    pass

# Função utilitária para pegar o DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()