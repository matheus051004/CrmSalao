from fastapi import APIRouter
from sqlalchemy import text

from app.database import SessionLocal, get_monthly_clientes_count
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
        clientes_count = db.query(Cliente).count()
        clientes_mes_count = db.execute(text("SELECT COUNT(*) FROM clientes WHERE created_at >= NOW() - INTERVAL '1 month'")).scalar()
        return {
            'clientes_count': clientes_count,
            'clientes_mes_count': clientes_mes_count,
            'clientes_jan' : monthly_clientes_count[0]['total'],
            # 'clientes_feb' : monthly_clientes_count[1][1],
            # 'clientes_mar' : monthly_clientes_count[2][1],
            # 'clientes_apr' : monthly_clientes_count[3][1],
            # 'clientes_may' : monthly_clientes_count[4][1],
            # 'clientes_jun' : monthly_clientes_count[5][1],
            # 'clientes_jul' : monthly_clientes_count[6][1],
            # 'clientes_aug' : monthly_clientes_count[7][1],
            # 'clientes_sep' : monthly_clientes_count[8][1],
            # 'clientes_oct' : monthly_clientes_count[9][1],
            # 'clientes_nov' : monthly_clientes_count[10][1],
            # 'clientes_dec' : monthly_clientes_count[11][1],
        }
    finally:
        db.close()