import os
from datetime import datetime

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

POSTGRES_HOST = os.environ.get("POSTGRES_HOST")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT")
POSTGRES_USER = os.environ.get("POSTGRES_USER")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD").replace('@', '%40')
DATABASE_NAME = os.environ.get("POSTGRES_DB")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{DATABASE_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def create_all_tables():
    Base.metadata.create_all(bind=engine)

# funções CRUD
def get_monthly_clientes_count():
    current_year = datetime.now().year
    db = SessionLocal()

    sql = f"""
    WITH meses AS (
    SELECT generate_series(1, 12) AS mes
),
clientes_por_mes AS (
    SELECT 
        EXTRACT(MONTH FROM created_at)::int AS mes,
        COUNT(*) AS total
    FROM clientes
    WHERE EXTRACT(YEAR FROM created_at) = {current_year}
    GROUP BY mes
)
SELECT 
    m.mes,
    COALESCE(c.total, 0) AS total
FROM meses m
LEFT JOIN clientes_por_mes c ON m.mes = c.mes
ORDER BY m.mes;
    """

    try:
        result = db.execute(text(sql))
        rows = result.fetchall()
        return [{"mes": row[0], "total": row[1]} for row in rows]
    finally:
        db.close()

def get_monthly_agendamentos_count():
    current_year = datetime.now().year
    db = SessionLocal()

    sql = f"""
    WITH meses AS (
    SELECT generate_series(1, 12) AS mes
),
agendamentos_por_mes AS (
    SELECT 
        EXTRACT(MONTH FROM created_at)::int AS mes,
        COUNT(*) AS total
    FROM agendamentos
    WHERE EXTRACT(YEAR FROM created_at) = {current_year} AND (status = 'agendado' OR status = 'concluido')
    GROUP BY mes
)
SELECT 
    m.mes,
    COALESCE(c.total, 0) AS total
FROM meses m
LEFT JOIN agendamentos_por_mes c ON m.mes = c.mes
ORDER BY m.mes;
    """

    try:
        result = db.execute(text(sql))
        rows = result.fetchall()
        return [{"mes": row[0], "total": row[1]} for row in rows]
    finally:
        db.close()

def get_today_agendamentos_count():
    db = SessionLocal()

    sql = """
    SELECT COUNT(*) FROM agendamentos WHERE DATE(created_at) = CURRENT_DATE
    """

    try:
        result = db.execute(text(sql))
        return result.scalar()
    finally:
        db.close()