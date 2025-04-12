from datetime import datetime

from fastapi import APIRouter
from sqlalchemy import text

from app.database import SessionLocal
from app.models.cliente import Cliente

router = APIRouter(
    prefix="/ajax",
    tags=["ajax"]
)


@router.get('/dashboard', name='ajax-dashboard')
async def dashboard():
    db = SessionLocal()
    try:
        monthly_clientes_count = get_monthly_clientes_count()
        monthly_agendamentos_count = get_monthly_agendamentos_count()
        clientes_count = db.query(Cliente).count()
        clientes_mes_count = db.execute(
            text("SELECT COUNT(*) FROM clientes WHERE created_at >= NOW() - INTERVAL '1 month'")).scalar()
        today_agendamentos = get_today_agendamentos_count()
        get_monthly_faturamento()
        return {
            'clientes_count': clientes_count,
            'clientes_mes_count': clientes_mes_count,
            'clientes_jan': monthly_clientes_count[0]['total'],
            'clientes_feb': monthly_clientes_count[1]['total'],
            'clientes_mar': monthly_clientes_count[2]['total'],
            'clientes_apr': monthly_clientes_count[3]['total'],
            'clientes_may': monthly_clientes_count[4]['total'],
            'clientes_jun': monthly_clientes_count[5]['total'],
            'clientes_jul': monthly_clientes_count[6]['total'],
            'clientes_aug': monthly_clientes_count[7]['total'],
            'clientes_sep': monthly_clientes_count[8]['total'],
            'clientes_oct': monthly_clientes_count[9]['total'],
            'clientes_nov': monthly_clientes_count[10]['total'],
            'clientes_dec': monthly_clientes_count[11]['total'],
            'agendamentos_jan': monthly_agendamentos_count[0]['total'],
            'agendamentos_feb': monthly_agendamentos_count[1]['total'],
            'agendamentos_mar': monthly_agendamentos_count[2]['total'],
            'agendamentos_apr': monthly_agendamentos_count[3]['total'],
            'agendamentos_may': monthly_agendamentos_count[4]['total'],
            'agendamentos_jun': monthly_agendamentos_count[5]['total'],
            'agendamentos_jul': monthly_agendamentos_count[6]['total'],
            'agendamentos_aug': monthly_agendamentos_count[7]['total'],
            'agendamentos_sep': monthly_agendamentos_count[8]['total'],
            'agendamentos_oct': monthly_agendamentos_count[9]['total'],
            'agendamentos_nov': monthly_agendamentos_count[10]['total'],
            'agendamentos_dec': monthly_agendamentos_count[11]['total'],
            'today_agendamentos': today_agendamentos,
        }
    finally:
        db.close()


def get_monthly_clientes_count(current_year=datetime.now().year) -> list[dict] | None:
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


def get_monthly_agendamentos_count(current_year=datetime.now().year) -> list[dict] | None:
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


def get_today_agendamentos_count() -> int | None:
    db = SessionLocal()
    date_today = datetime.now().date()
    sql = f"""
    SELECT COUNT(*) FROM agendamentos WHERE DATE(created_at) = '{date_today}'
    """

    try:
        result = db.execute(text(sql))
        return result.scalar()
    finally:
        db.close()


def get_monthly_faturamento(current_year=datetime.now().year) -> list[dict] | None:
    for month in range(1, 13):
        db = SessionLocal()
        sql = f"""
            SELECT * FROM agendamentos WHERE status = 'concluido' AND EXTRACT(MONTH FROM created_at) = {month} AND EXTRACT(YEAR FROM created_at) = {current_year}
        """
        try:
            result = db.execute(text(sql))
            agendamentos = result.fetchall()
            print(agendamentos)
        finally:
            db.close()
