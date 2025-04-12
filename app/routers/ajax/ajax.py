from datetime import datetime

from fastapi import APIRouter
from sqlalchemy import text

from app import Servico, Profissional, Agendamento
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
            'monthly_faturamento': get_monthly_year_faturamento(),
            'monthly_faturamento_previsto': get_monthly_year_faturamento_previsto(),
            'month_faturamento': get_month_faturamento(),
        }
    finally:
        db.close()


@router.get('/profissionals-agendamentos-graph', name='pa-graph')
async def profissionals_agendamentos_graph(interval_query: str = 'month'):
    db = SessionLocal()
    try:
        return get_agendamentos_from_all_profissionals(interval_query)
    finally:
        db.close()


# funções db
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


def get_monthly_year_faturamento(current_year=datetime.now().year) -> list[float] | None:
    """
    Função para calcular o faturamento mensal de um ano específico.
    :param current_year:
    :return:
    """
    months_faturamento = []
    for month in range(1, 13):
        faturamento = 0

        db = SessionLocal()
        sql = f"""
            SELECT * FROM agendamentos WHERE status = 'concluido' AND EXTRACT(MONTH FROM created_at) = {month} AND EXTRACT(YEAR FROM created_at) = {current_year}
        """
        try:
            result = db.execute(text(sql))
            agendamentos = [dict(row._mapping) for row in result.fetchall()]

            for agendamento in agendamentos:
                for servico_id in agendamento['servicos']:
                    servico = db.query(Servico).filter_by(id=servico_id).first()
                    faturamento += float(servico.price)

            months_faturamento.append(faturamento)
        finally:
            db.close()

    return months_faturamento


def get_monthly_year_faturamento_previsto(current_year=datetime.now().year) -> list[float] | None:
    """
    Função para calcular o faturamento mensal de um ano específico, previsto.
    :param current_year:
    :return:
    """
    months_faturamento = []
    for month in range(1, 13):
        faturamento = 0

        db = SessionLocal()
        sql = f"""
            SELECT * FROM agendamentos WHERE EXTRACT(MONTH FROM created_at) = {month} AND EXTRACT(YEAR FROM created_at) = {current_year}
        """
        try:
            result = db.execute(text(sql))
            agendamentos = [dict(row._mapping) for row in result.fetchall()]

            for agendamento in agendamentos:
                for servico_id in agendamento['servicos']:
                    servico = db.query(Servico).filter_by(id=servico_id).first()
                    faturamento += float(servico.price)

            months_faturamento.append(faturamento)
        finally:
            db.close()

    return months_faturamento


def get_month_faturamento(month=datetime.now().month, current_year=datetime.now().year) -> float | None:
    """
    Função para calcular o faturamento mensal de um ano e mês específico.
    :param month:
    :param current_year:
    :return:
    """
    faturamento = 0

    db = SessionLocal()
    sql = f"""
        SELECT * FROM agendamentos WHERE status = 'concluido' AND EXTRACT(MONTH FROM created_at) = {month} AND EXTRACT(YEAR FROM created_at) = {current_year}
    """
    try:
        result = db.execute(text(sql))
        agendamentos = [dict(row._mapping) for row in result.fetchall()]

        for agendamento in agendamentos:
            for servico_id in agendamento['servicos']:
                servico = db.query(Servico).filter_by(id=servico_id).first()
                faturamento += float(servico.price)
        return faturamento
    finally:
        db.close()


def get_agendamentos_from_profissional(profissional_id: int, interval_query: str = 'month') -> list[Agendamento] | None:
    """
    Função para obter agendamentos de um profissional específico.
    :param interval_query: Intervalo de consulta
    :param profissional_id: ID do profissional
    :return:
    """
    db = SessionLocal()
    current_year = datetime.now().year
    sql = ''

    if interval_query == 'month':
        month = datetime.now().month
        sql = f"""
            SELECT * FROM agendamentos WHERE EXTRACT(MONTH FROM created_at) = {month} AND EXTRACT(YEAR FROM created_at) = {current_year} AND profissional_id = {profissional_id}
        """
    elif interval_query == 'week':
        sql = f"""
            SELECT * FROM agendamentos WHERE created_at >= NOW() - INTERVAL '7 days' AND profissional_id = {profissional_id}
        """
    elif interval_query == 'day':
        sql = f"""
            SELECT * FROM agendamentos WHERE DATE(created_at) = DATE(NOW()) AND profissional_id = {profissional_id}
        """
    try:
        result = db.execute(text(sql))
        agendamentos = [Agendamento(**dict(row._mapping)) for row in result.fetchall()]
        return agendamentos
    finally:
        db.close()


def get_agendamentos_from_all_profissionals(interval_query: str = 'month') -> list[dict] | None:
    """
    Função para obter agendamentos de todos os profissionais.
    :return:
    """
    profissionals_agndmts = []
    db = SessionLocal()
    try:
        profissionals = db.query(Profissional).all()

        for profissional in profissionals:
            profissionals_agndmts.append({
                'profissional': profissional.name,
                'agendamentos': get_agendamentos_from_profissional(profissional.id, interval_query),
            })
    finally:
        db.close()

    return profissionals_agndmts
