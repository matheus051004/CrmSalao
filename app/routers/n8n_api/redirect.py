from fastapi.routing import APIRouter
from sqlalchemy import text

from app.database import SessionLocal

redirect_router = APIRouter(
    prefix="/redirect",
    include_in_schema=True,
)


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


def response(success=True, message="", data=None):
    """
    Formata a resposta da API.
    """
    return {
        "success": success,
        "message": message,
        "data": data
    }
