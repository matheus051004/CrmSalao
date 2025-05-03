from fastapi import APIRouter

from app.jinja import app_settings

config_router = APIRouter(
    prefix="/configs",
    include_in_schema=True,
)


@config_router.get("/")
async def configs():
    configs = {
        'salao_name': app_settings('salao_name'),
    }
    return response(success=True, message="ok", data=configs)


def response(success=True, message="", data=None):
    """
    Formata a resposta da API.
    """
    return {
        "success": success,
        "message": message,
        "data": data
    }
