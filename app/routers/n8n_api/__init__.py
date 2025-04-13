from fastapi import APIRouter

n8n_api_router = APIRouter(
    prefix="/n8n-api",
    tags=["n8n-api"],
    include_in_schema=True,
)

from app.routers.n8n_api import agendamentos

n8n_api_router.include_router(agendamentos.agendamentos_router)


def response(success=True, message="", data=None):
    """
    Formata a resposta da API.
    """
    return {
        "success": success,
        "message": message,
        "data": data
    }
