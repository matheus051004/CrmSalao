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
        clientes_count = db.query(Cliente).count()
        clientes_mes_count = db.query(text("SELECT COUNT(*) FROM clientes WHERE created_at >= NOW() - INTERVAL '1 month'")).scalar()
        return {
            'clientes_count': clientes_count,
            'clientes_mes_count': clientes_mes_count,
        }
    finally:
        db.close()