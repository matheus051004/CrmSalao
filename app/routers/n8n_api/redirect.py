import os

from fastapi.routing import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from app.Evolution import Evolution
from app.database import SessionLocal

redirect_router = APIRouter(
    prefix="/redirect",
    include_in_schema=True,
)


class ToHuman(BaseModel):
    telefone: str


@redirect_router.get("/in-human/{idd}", name="n8n-in-human")
async def in_human(idd):
    db = SessionLocal()
    try:
        result = db.execute(text(f"SELECT * FROM human_support WHERE id = {idd} OR telefone = '{idd}'"))
        rows = result.mappings().all()
        if len(rows) == 0:
            return response(False, "ID não encontrado", {
                "exist": False,
            })
        else:
            return response(True, "O cliente está no suporte humano", {
                "exist": True,
                "data": rows[0]
            })
    finally:
        db.close()


@redirect_router.post('/to-human', name="n8n-to-human")
async def to_human(to_human: ToHuman):
    db = SessionLocal()
    try:
        db.execute(text(f"DELETE FROM human_support WHERE id = {to_human.telefone} OR telefone = '{to_human.telefone}'"))
        db.execute(text('INSERT INTO human_support (telefone) VALUES (:telefone)'), {"telefone": to_human.telefone})
        db.commit()

        # Enviar mensagem para o admin
        ev = Evolution(os.environ.get('WAHA_API_URL'), os.environ.get('WAHA_API_KEY'),
                       os.environ.get('WAHA_INSTANCE'))
        ev.simple_text(os.environ.get('WHATSAPP_ADMIN_NUMBER'), f"⚠ O número {to_human.telefone} está aguardando atendimento humano.")

        return response(True, "Cliente enviado para o suporte humano")
    finally:
        db.close()


@redirect_router.post('/to-ia', name="n8n-to-ia")
async def to_ia(to_human: ToHuman):
    db = SessionLocal()
    try:
        db.execute(text(f"DELETE FROM human_support WHERE id = {to_human.telefone} OR telefone = '{to_human.telefone}'"))
        db.commit()

        return response(True, "Cliente enviado para o suporte IA")
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
