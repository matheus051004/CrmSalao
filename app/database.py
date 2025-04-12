import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

POSTGRES_HOST = os.environ.get("POSTGRES_HOST")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT")
POSTGRES_USER = os.environ.get("POSTGRES_USER")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD").replace('@', '%40')
DATABASE_NAME = os.environ.get("POSTGRES_DB")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{DATABASE_NAME}"

# Configurar o engine com pool de conexões
engine = create_engine(
    DATABASE_URL,
    pool_size=5,               # Número máximo de conexões permanentes
    max_overflow=10,           # Conexões adicionais permitidas quando o pool está cheio
    pool_timeout=30,           # Tempo (segundos) para esperar por uma conexão
    pool_recycle=1800,         # Reconectar após 30 minutos (1800 segundos) de inatividade
    pool_pre_ping=True,        # Testar se a conexão está ativa antes de usar
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def create_all_tables():
    Base.metadata.create_all(bind=engine)

# Criar uma dependência para usar nas rotas
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()