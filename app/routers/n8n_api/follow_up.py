import os

from fastapi.routing import APIRouter

from app import Cliente
from app.Evolution import Evolution
from app.jinja import app_settings, get_servicos_string
from app.database import SessionLocal
from sqlalchemy import text

follow_up_router = APIRouter(
    prefix="/follow-up",
    include_in_schema=True,
)


@follow_up_router.get("/", name="n8n-follow-up")
async def follow_up():
    """
    Endpoint para o n8n.
    """

    # lembrete de agendamentos para os clientes X minutos antes
    minutes_follow_up = app_settings("follow_up_minutes", 5)
    db = SessionLocal()
    try:
        # Agendamentos que estão próximos
        from datetime import datetime, timedelta

        # Calcula o tempo limite usando Python
        current_time = datetime.now()
        limit_time = current_time + timedelta(minutes=int(minutes_follow_up))

        query = db.execute(
            text("""
                SELECT * FROM agendamentos 
                WHERE start <= :limit_time
                AND notified = false
                AND status = 'agendado'
            """),
            {"limit_time": limit_time}
        )
        result_proxy = query.mappings()  # Isso retorna dicionários em vez de tuplas
        agendamentos = result_proxy.all()
        if agendamentos:
            ev = Evolution(os.environ.get('WAHA_API_URL'), os.environ.get('WAHA_API_KEY'),
                           os.environ.get('WAHA_INSTANCE'))

            for agendamento in agendamentos:
                cliente = db.query(Cliente).filter(Cliente.id == agendamento['cliente_id']).first()
                msg = app_settings('msg_follow_up')
                msg_prepared = (msg.replace('{cliente_name}', cliente.name)
                                .replace('{salao_name}', app_settings('salao_name'))
                                .replace('{servico_date}', agendamento['start'].strftime('%d/%m/%Y %H:%M'))
                                .replace('{servico_name}', get_servicos_string(agendamento['servicos'])))

                # Atualiza o agendamento para notificado
                db.execute(
                    text("""
                        UPDATE agendamentos 
                        SET notified = true 
                        WHERE id = :agendamento_id
                    """),
                    {"agendamento_id": agendamento['id']}
                )
                db.commit()

                ev.simple_text(cliente.phone, msg_prepared)
    finally:
        db.close()

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
