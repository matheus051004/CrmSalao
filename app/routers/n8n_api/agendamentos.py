from fastapi.routing import APIRouter

agendamentos_router = APIRouter(
    prefix="/agendamentos",
    include_in_schema=True,
)

@agendamentos_router.get("/horarios-diponiveis", name="n8n-horarios-diponiveis")
async def horarios_diponiveis(date: str):
    """
    Retorna os horários disponíveis para agendamentos.
    """
    return {
        "status": "success",
        "message": "Horários disponíveis retornados com sucesso.",
        "data": [
            {
                "id": 1,
                "start_time": "2023-10-01T09:00:00",
                "end_time": "2023-10-01T10:00:00"
            },
            {
                "id": 2,
                "start_time": "2023-10-01T10:00:00",
                "end_time": "2023-10-01T11:00:00"
            }
        ]
    }