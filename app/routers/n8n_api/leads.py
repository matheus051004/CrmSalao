from fastapi import APIRouter

from app import Cliente
from app.database import SessionLocal
from app.models.pydantic.api.LeadCreate import LeadCreate

leads_router = APIRouter(
    prefix="/leads",
    include_in_schema=True,
)


@leads_router.post("/create")
async def create(lead_create: LeadCreate):
    db = SessionLocal()
    try:
        cliente = db.query(Cliente).filter(Cliente.phone == lead_create.phone).first()
        if cliente:
            return response(False, "Lead já existe")

        cliente = Cliente(
            name=lead_create.name,
            email=lead_create.email,
            phone=lead_create.phone,
        )
        db.add(cliente)
        db.commit()
        return response(True, "Lead registrado com sucesso")
    finally:
        db.close()


@leads_router.get('/cliente/{idd}')
async def get_cliente(idd: int):
    db = SessionLocal()
    try:
        cliente = db.query(Cliente).filter(Cliente.id == idd).first()
        if not cliente:
            return response(False, "Cliente não encontrado")
        return response(True, "ok", cliente)
    finally:
        db.close()


def response(success=True, message="", data=None):
    """
    Formata a resposta da API.
    """
    return {
        "success": success,
        "message": message,
        "data": data
    }
