from fastapi import APIRouter

from app import Profissional
from app.database import SessionLocal
from app.jinja import app_settings, get_servicos_string

config_router = APIRouter(
    prefix="/configs",
    include_in_schema=True,
)


@config_router.get("/")
async def configs():
    configs = {
        'salao_name': app_settings('salao_name'),
        'salao_slogan': app_settings('salao_slogan'),
        'assistant_name': app_settings('assistant_name'),
    }
    return response(success=True, message="ok", data=configs)

@config_router.get("/profissionais")
async def profissionais():
    """
    Retorna os profissionais cadastrados no sistema.
    """
    db = SessionLocal()
    try:
        profissionais = db.query(Profissional).all()
        if not profissionais:
            return response(success=False, message="Nenhum profissional encontrado", data=[])

        # Formata a resposta
        data = []
        for profissional in profissionais:
            data.append({
                "id": profissional.id,
                "nome": profissional.name,
                "servicos": get_servicos_string(profissional.services),
            })

        return response(success=True, message="ok", data=data)
    finally:
        db.close()


@config_router.get('/profissional-horarios/{profissional_id}')
async def profissional_horarios(profissional_id: int):
    """
    Retorna os horários de atendimento de um profissional.
    """
    db = SessionLocal()
    try:
        profissional = db.query(Profissional).filter(Profissional.id == profissional_id).first()
        if not profissional:
            return response(success=False, message="Nenhum profissional encontrado", data=[])

        # Formata a resposta
        horarios = {
            "segunda": profissional.horarios["0"],
            "terca": profissional.horarios["1"],
            "quarta": profissional.horarios["2"],
            "quinta": profissional.horarios["3"],
            "sexta": profissional.horarios["4"],
            "sabado": profissional.horarios["5"],
            "domingo": profissional.horarios["6"],
        }

        return response(success=True, message="ok", data=horarios)
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
