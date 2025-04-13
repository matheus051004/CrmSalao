from fastapi import APIRouter, HTTPException

from app import Cliente, Agendamento
from app.database import SessionLocal

router = APIRouter(
    prefix="/ajax-clientes",
    include_in_schema=False
)

@router.delete('delete-cliente/{cliente_id}', name='ajax-delete-cliente')
async def delete_cliente(cliente_id: int):
    """
    Delete a client by ID.
    """
    db = SessionLocal()
    try:
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if not cliente:
            return {"status": 404, "message": f"Cliente with ID {cliente_id} not found."}

        delete_cliente_related_data(cliente_id)
        db.delete(cliente)
        db.commit()
    finally:
        db.close()
    return {"status": 200, "message": f"Cliente with ID {cliente_id} deleted."}


# db functions
def delete_cliente_related_data(cliente_id: int):
    """
    Delete related data for a client.
    """
    db = SessionLocal()
    try:
        # agendamentos
        db.query(Agendamento).filter(Agendamento.cliente_id == cliente_id).delete()
        db.commit()
    finally:
        db.close()