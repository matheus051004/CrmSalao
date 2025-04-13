from datetime import datetime, timedelta

from fastapi.routing import APIRouter

from app import Servico, Profissional
from app.database import SessionLocal

from app.models.agendamentos import Agendamento

agendamentos_router = APIRouter(
    prefix="/agendamentos",
    include_in_schema=True,
)


@agendamentos_router.get("/horarios-diponiveis", name="n8n-horarios-diponiveis")
async def horarios_diponiveis(date: str, profissional_id: int, servico_id: int):
    """
    Retorna os horários disponíveis para agendamentos de um serviço.
    """

    try:
        from datetime import datetime, timedelta, time
        data = datetime.strptime(date, '%Y-%m-%d')
        dia_semana = str(data.weekday())  # 0-6, onde 0 é segunda-feira
    except ValueError:
        return response(False, "Formato de data inválido, use YYYY-MM-DD")

    db = SessionLocal()
    try:
        servico = db.query(Servico).filter(Servico.id == servico_id).first()
        if not servico:
            return response(False, "Serviço não encontrado")

        profissional: Profissional = db.query(Profissional).filter(Profissional.id == profissional_id).first()
        if not profissional:
            return response(False, "Profissional não encontrado")

        # verificar se o profissional atende o serviço
        if servico_id not in profissional.services:
            return response(False, "Profissional não atende este serviço")

        servico_duration = servico.minutes

        # Verificar se o profissional trabalha neste dia da semana
        horarios_do_dia = profissional.horarios.get(dia_semana, [])
        if not horarios_do_dia:
            return response(False, "Profissional não atende neste dia da semana")

        # Busca agendamentos existentes do profissional nessa data
        inicio_dia = datetime.combine(data, time(0, 0, 0))
        fim_dia = datetime.combine(data, time(23, 59, 59))

        agendamentos_existentes = db.query(Agendamento).filter(
            Agendamento.profissional_id == profissional_id,
            Agendamento.start >= inicio_dia,
            Agendamento.end <= fim_dia,
            Agendamento.status != 'cancelado'
        ).all()

        # Constrói lista de horários ocupados
        horarios_ocupados = []
        for agendamento in agendamentos_existentes:
            horarios_ocupados.append({
                'inicio': agendamento.start,
                'fim': agendamento.end
            })

        # Cria slots disponíveis a cada 30 minutos dentro dos horários de trabalho
        horarios_disponiveis = []
        intervalo_minutos = 30  # Intervalo padrão entre slots

        for periodo in horarios_do_dia:
            hora_inicio = datetime.strptime(periodo['inicio'], '%H:%M').time()
            hora_fim = datetime.strptime(periodo['fim'], '%H:%M').time()

            # Combina a data com os horários de início e fim
            inicio_periodo = datetime.combine(data, hora_inicio)
            fim_periodo = datetime.combine(data, hora_fim)

            # Cria slots a cada 30 minutos
            slot_atual = inicio_periodo
            while slot_atual + timedelta(minutes=servico_duration) <= fim_periodo:
                slot_fim = slot_atual + timedelta(minutes=servico_duration)

                # Verifica se o slot está disponível (não colide com nenhum agendamento)
                disponivel = True
                for ocupado in horarios_ocupados:
                    # Se há alguma sobreposição entre o slot e um horário ocupado
                    if slot_atual < ocupado['fim'] and slot_fim > ocupado['inicio']:
                        disponivel = False
                        break

                if disponivel:
                    horarios_disponiveis.append({
                        'start': slot_atual.strftime('%H:%M'),
                        'end': slot_fim.strftime('%H:%M'),
                        # 'data': date
                    })

                # Avança para o próximo slot
                slot_atual += timedelta(minutes=intervalo_minutos)

        return response(True, "Horários disponíveis", horarios_disponiveis)

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
