from fastapi import APIRouter
from sqlalchemy import text

from app.database import SessionLocal, get_monthly_clientes_count, get_monthly_agendamentos_count
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
        clientes_mes_count = db.execute(text("SELECT COUNT(*) FROM clientes WHERE created_at >= NOW() - INTERVAL '1 month'")).scalar()
        return {
            'clientes_count': clientes_count,
            'clientes_mes_count': clientes_mes_count,
            'clientes_jan' : monthly_clientes_count[0]['total'],
            'clientes_feb' : monthly_clientes_count[1]['total'],
            'clientes_mar' : monthly_clientes_count[2]['total'],
            'clientes_apr' : monthly_clientes_count[3]['total'],
            'clientes_may' : monthly_clientes_count[4]['total'],
            'clientes_jun' : monthly_clientes_count[5]['total'],
            'clientes_jul' : monthly_clientes_count[6]['total'],
            'clientes_aug' : monthly_clientes_count[7]['total'],
            'clientes_sep' : monthly_clientes_count[8]['total'],
            'clientes_oct' : monthly_clientes_count[9]['total'],
            'clientes_nov' : monthly_clientes_count[10]['total'],
            'clientes_dec' : monthly_clientes_count[11]['total'],
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
            'agendamentos_dec': monthly_agendamentos_count[11]['total']
        }
    finally:
        db.close()