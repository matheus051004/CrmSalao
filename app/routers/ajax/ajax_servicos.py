from fastapi import APIRouter
from fastapi import Request
from sqlalchemy import text

from app import Servico, Agendamento, Profissional
from app.database import SessionLocal

router = APIRouter(
    prefix="/ajax-servicos",
    include_in_schema=False
)


@router.delete('delete-servico', name='ajax-delete-servico')
async def delete_servico(request: Request):
    json = await request.json()
    db = SessionLocal()
    try:
        servico = db.query(Servico).filter(Servico.id == json.servico_id).first()

        if not servico:
            return response(False, 'Serviço não encontrado', None)

        if check_profissional_using_servico(servico.id):
            return response(False, 'O Serviço está sendo usado por um profissional', None)

        delete_related_agendamentos(servico.id)

        db.delete(servico)
        db.commit()
    finally:
        db.close()
    return response(True, f"Serviço com ID {servico.id} deletado.")


def delete_related_agendamentos(servico_id):
    db = SessionLocal()
    try:
        agendamentos = db.query(Agendamento).filter(text(f"servicos @> '[{servico_id}]'::jsonb")).all()
        for agendamento in agendamentos:
            db.delete(agendamento)
        db.commit()
    finally:
        db.close()


def check_profissional_using_servico(servico_id) -> bool | None:
    db = SessionLocal()
    try:
        profissionais = db.query(Profissional).filter(text(f"services @> '[{servico_id}]'::jsonb")).all()
        if profissionais:
            return True
        return False
    finally:
        db.close()


def response(success=True, message="", data=None):
    return {
        "success": success,
        "message": message,
        "data": data
    }
