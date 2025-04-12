from fastapi import APIRouter
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
        return {
            'clientes_count': clientes_count
        }
    finally:
        db.close()