import os

from fastapi import APIRouter
from app import Cliente, Agendamento, Profissional
from app.database import SessionLocal
from app.models.pydantic.ajax.AgendamentoComplete import AgendamentoComplete
from app.GoogleCalendarManager import GoogleCalendarManager
from app.Evolution import Evolution
from app.jinja import app_settings, get_servicos_string

router = APIRouter(
    prefix="/ajax-agendamentos",
    include_in_schema=False
)


@router.post('/concluir', name='ajax-concluir-agendamento')
async def concluir_agendamento(agendamento_confirm: AgendamentoComplete):
    db = SessionLocal()
    try:
        agendamento = db.query(Agendamento).filter(Agendamento.id == agendamento_confirm.agendamento_id,
                                                   Agendamento.status == 'agendado').first()
        if not agendamento:
            return response(False, 'Agendamento não encontrado ou já foi concluído')

        profissional = db.query(Profissional).filter(Profissional.id == agendamento.profissional_id).first()
        if not profissional:
            raise response(False, 'Profissional não encontrado')

        agendamento.status = 'concluido'
        db.commit()

        # Google Calendar
        gcm = GoogleCalendarManager(profissional.calendar_id, os.environ.get('GOOGLE_CREDENTIAL_JSON_B64'))
        gcm.delete_event(agendamento.google_event_id)

        # notificar
        if agendamento_confirm.notify_cliente:
            cliente = db.query(Cliente).filter(Cliente.id == agendamento.cliente_id).first()
            if cliente:
                msg_prepared = (agendamento_confirm.message
                                .replace('{cliente_name}', cliente.name)
                                .replace('{salao_name}', app_settings('salao_name')))

                ev = Evolution(os.environ.get('EVOLUTION_API_URL'), os.environ.get('EVOLUTION_API_KEY'),
                               os.environ.get('EVOLUTION_INSTANCE'))
                ev.simple_text(cliente.phone, msg_prepared)

        return response(True, 'Agendamento finalizado com sucesso')
    finally:
        db.close()


@router.post('/cancelar', name='ajax-cancelar-agendamento')
async def cancelar_agendamento(agendamento_confirm: AgendamentoComplete):
    db = SessionLocal()
    try:
        agendamento = db.query(Agendamento).filter(Agendamento.id == agendamento_confirm.agendamento_id,
                                                   Agendamento.status == 'agendado').first()
        if not agendamento:
            return response(False, 'Agendamento não encontrado ou já foi concluído')

        profissional = db.query(Profissional).filter(Profissional.id == agendamento.profissional_id).first()
        if not profissional:
            raise response(False, 'Profissional não encontrado')

        agendamento.status = 'cancelado'
        db.commit()

        # Google Calendar
        gcm = GoogleCalendarManager(profissional.calendar_id, os.environ.get('GOOGLE_CREDENTIAL_JSON_B64'))
        gcm.delete_event(agendamento.google_event_id)

        # notificar
        if agendamento_confirm.notify_cliente:
            cliente = db.query(Cliente).filter(Cliente.id == agendamento.cliente_id).first()
            if cliente:
                msg_prepared = (agendamento_confirm.message
                                .replace('{cliente_name}', cliente.name)
                                .replace('{salao_name}', app_settings('salao_name'))
                                .replace('{servico_name}', get_servicos_string(agendamento.servicos)))

                ev = Evolution(os.environ.get('EVOLUTION_API_URL'), os.environ.get('EVOLUTION_API_KEY'),
                               os.environ.get('EVOLUTION_INSTANCE'))
                ev.simple_text(cliente.phone, msg_prepared)

        return response(True, 'Agendamento finalizado com sucesso')
    finally:
        db.close()


def replace_placeholders(text, salao_name = '', cliente_name = '', profissional_name = ''):
    text = text.replace('{salao_name}', salao_name)
    text = text.replace('{cliente_name}', cliente_name)
    text = text.replace('{profissional_name}', profissional_name)
    return text



def response(success=True, message="", data=None):
    return {
        "success": success,
        "message": message,
        "data": data
    }
