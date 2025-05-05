from fastapi.routing import APIRouter

follow_up_router = APIRouter(
    prefix="/follow-up",
    include_in_schema=True,
)


@follow_up_router.get("/", name="n8n-follow-up")
async def follow_up():
    """
    Endpoint para o n8n.
    """
    return response(success=True, message="OK", data=None)


def response(success=True, message="", data=None):
    """
    Formata a resposta da API.
    """
    return {
        "success": success,
        "message": message,
        "data": data
    }
