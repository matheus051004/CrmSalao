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
        print(get_monthly_clientes_count())
        clientes_count = db.query(Cliente).count()
        clientes_mes_count = db.execute(text("SELECT COUNT(*) FROM clientes WHERE created_at >= NOW() - INTERVAL '1 month'")).scalar()
        return {
            'clientes_count': clientes_count,
            'clientes_mes_count': clientes_mes_count,
        }
    finally:
        db.close()