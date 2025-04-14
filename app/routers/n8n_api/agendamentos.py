import os
from datetime import datetime, time, timedelta
from typing import Tuple, Any, Optional, List, Dict

from fastapi.routing import APIRouter
from sqlalchemy import func

from app import Servico, Profissional
from app.database import SessionLocal
from app.models.agendamentos import Agendamento
from app.models.pydantic.AgendamentoCancel import AgendamentoCancel
from app.models.pydantic.AgendamentoCreate import AgendamentoCreate
from app.GoogleCalendarManager import GoogleCalendarManager
from app.models.pydantic.AgendamentoReschedule import AgendamentoReschedule

agendamentos_router = APIRouter(
    prefix="/agendamentos",
    include_in_schema=True,
)


@agendamentos_router.get("/horarios-diponiveis", name="n8n-horarios-diponiveis")
async def horarios_diponiveis(date: str, profissional_id: int, servicos_ids: str):
    """Retorna os horários disponíveis para agendamentos de múltiplos serviços.
    :arg date: Data do agendamento no formato YYYY-MM-DD
    :arg profissional_id: ID do profissional
    :arg servicos_ids: IDs dos serviços separados por vírgula
    """
    # Validar a data
    sucesso, resultado = validar_data(date)
    if not sucesso:
        return response(False, resultado)

    data, dia_semana = resultado

    db = SessionLocal()
    servicos_ids = [int(idd.strip()) for idd in servicos_ids.split(",")]
    try:
        # Verificar disponibilidade do profissional
        sucesso, resultado, profissional, servicos, duracao_total = verificar_disponibilidade_profissional(
            db, profissional_id, servicos_ids, dia_semana
        )
        if not sucesso:
            return response(False, resultado)

        horarios_do_dia = resultado

        # Obter agendamentos existentes
        horarios_ocupados = obter_agendamentos_existentes(db, profissional_id, data)

        # Gerar slots disponíveis
        horarios_disponiveis = gerar_slots_disponiveis(
            data, horarios_do_dia, duracao_total, horarios_ocupados
        )

        return response(True, "Horários disponíveis", horarios_disponiveis)
    finally:
        db.close()


@agendamentos_router.post("/criar", name="n8n-criar-agendamento")
async def criar_agendamento(dados: AgendamentoCreate):
    cliente_id = dados.cliente_id
    profissional_id = dados.profissional_id
    servicos_ids = dados.servicos_ids
    date = dados.date
    start_hour = dados.start_hour
    metadata = dados.metadata

    description = "\n".join([f"{key}: {value}" for key, value in metadata.items()]) if metadata else ""

    # Validar a data
    sucesso, resultado = validar_data(date)
    if not sucesso:
        return response(False, resultado)

    data_obj, dia_semana = resultado

    db = SessionLocal()
    try:
        # 1. Verificar se o profissional atende todos os serviços e trabalha naquele dia
        sucesso, resultado, profissional, servicos, duracao_total = verificar_disponibilidade_profissional(
            db, profissional_id, servicos_ids, dia_semana
        )
        if not sucesso:
            return response(False, resultado)

        horarios_do_dia = resultado

        # 2. Verificar se o horário escolhido está dentro do período de trabalho do profissional
        try:
            hora_inicio = datetime.strptime(start_hour, '%H:%M').time()
            inicio_agendamento = datetime.combine(data_obj, hora_inicio)
            fim_agendamento = inicio_agendamento + timedelta(minutes=duracao_total)
        except ValueError:
            return response(False, "Formato de horário inválido, use HH:MM")

        # Verificar se está no horário de atendimento do profissional
        horario_valido = False
        for periodo in horarios_do_dia:
            hora_inicio_periodo = datetime.strptime(periodo['inicio'], '%H:%M').time()
            hora_fim_periodo = datetime.strptime(periodo['fim'], '%H:%M').time()

            inicio_periodo = datetime.combine(data_obj, hora_inicio_periodo)
            fim_periodo = datetime.combine(data_obj, hora_fim_periodo)

            if inicio_agendamento >= inicio_periodo and fim_agendamento <= fim_periodo:
                horario_valido = True
                break

        if not horario_valido:
            return response(False, "Horário fora do período de atendimento do profissional")

        # 3. Verificar se o horário está livre (não colide com outros agendamentos)
        horarios_ocupados = obter_agendamentos_existentes(db, profissional_id, data_obj)

        for ocupado in horarios_ocupados:
            # Se há alguma sobreposição entre o agendamento pretendido e um horário ocupado
            if inicio_agendamento < ocupado['fim'] and fim_agendamento > ocupado['inicio']:
                return response(False, "Horário indisponível, já existe agendamento neste período")

        # Preparar nomes dos serviços para o título automático
        nomes_servicos = ", ".join([servico.name for servico in servicos])
        titulo_auto = f"{nomes_servicos}"

        # Criar o agendamento
        novo_agendamento = Agendamento(
            cliente_id=cliente_id,
            profissional_id=profissional_id,
            servicos=servicos_ids,
            start=inicio_agendamento,
            end=fim_agendamento,
            title=titulo_auto,
            description=description,
            status="agendado",
            client_metadata=metadata
        )

        db.add(novo_agendamento)
        db.commit()
        db.refresh(novo_agendamento)

        # google calendar
        gcm = GoogleCalendarManager(profissional.calendar_id, os.environ.get('GOOGLE_CREDENTIAL_JSON_B64'))
        idd, htmlLink = gcm.create_event(
            summary=titulo_auto,
            start_time=inicio_agendamento,
            end_time=fim_agendamento,
            description=description,
        )
        novo_agendamento.google_event_id = idd
        db.add(novo_agendamento)
        db.commit()

        return response(
            True,
            "Agendamento criado com sucesso",
            {
                "id": novo_agendamento.id,
                "inicio": novo_agendamento.start.strftime('%Y-%m-%d %H:%M'),
                "fim": novo_agendamento.end.strftime('%Y-%m-%d %H:%M'),
                "servicos": nomes_servicos,
                "profissional": profissional.name
            }
        )

    except Exception as e:
        db.rollback()
        return response(False, f"Erro ao criar agendamento: {str(e)}")
    finally:
        db.close()


@agendamentos_router.post('/cancelar', name='n8n-cancelar-agendamento')
async def cancelar_agendamento(agendamento_cancel: AgendamentoCancel):
    agendamento_id = agendamento_cancel.agendamento_id
    cliente_id = agendamento_cancel.cliente_id

    db = SessionLocal()
    try:
        # Verifica se o agendamento existe
        agendamento = db.query(Agendamento).filter(Agendamento.id == agendamento_id).first()
        if not agendamento:
            return response(False, "Agendamento não encontrado")

        # Verifica se o cliente é o dono do agendamento
        if agendamento.cliente_id != cliente_id:
            return response(False, "Você não tem permissão para cancelar este agendamento")

        # Cancela o agendamento
        agendamento.status = 'cancelado'
        db.commit()

        profissional = db.query(Profissional).filter(Profissional.id == agendamento.profissional_id).first()

        # Remove o evento do Google Calendar
        gcm = GoogleCalendarManager(profissional.calendar_id, os.environ.get('GOOGLE_CREDENTIAL_JSON_B64'))
        gcm.delete_event(agendamento.google_event_id)

        return response(True, "Agendamento cancelado com sucesso")
    finally:
        db.close()


@agendamentos_router.post('/reagendar', name='n8n-reagendar-agendamento')
async def reagendar_agendamento(agendamento_reschedule: AgendamentoReschedule):
    agendamento_id = agendamento_reschedule.agendamento_id
    cliente_id = agendamento_reschedule.cliente_id

    date = datetime.strptime(agendamento_reschedule.new_date_time, '%Y-%m-%d %H:%M')
    dia_semana = str(date.weekday())

    db = SessionLocal()
    try:
        agendamento = db.query(Agendamento).filter(Agendamento.id == agendamento_id,
                                                   Agendamento.status == 'agendado').first()
        if not agendamento:
            return response(False, "Agendamento não encontrado")

        if agendamento.cliente_id != cliente_id:
            return response(False, "Você não tem permissão para reagendar este evento")

        # 1. Verificar se o profissional atende todos os serviços e trabalha naquele dia
        sucesso, resultado, profissional, servicos, duracao_total = verificar_disponibilidade_profissional(
            db, agendamento.profissional_id, agendamento.servicos, dia_semana
        )
        if not sucesso:
            return response(False, resultado)
        horarios_do_dia = resultado

        # 2. Verificar se o horário escolhido está dentro do período de trabalho do profissional
        try:
            fim_agendamento = date + timedelta(minutes=duracao_total)
        except ValueError:
            return response(False, "Formato de horário inválido, use HH:MM")

        # Verificar se está no horário de atendimento do profissional
        horario_valido = False
        for periodo in horarios_do_dia:
            hora_inicio_periodo = datetime.strptime(periodo['inicio'], '%H:%M').time()
            hora_fim_periodo = datetime.strptime(periodo['fim'], '%H:%M').time()
            inicio_periodo = datetime.combine(date, hora_inicio_periodo)
            fim_periodo = datetime.combine(date, hora_fim_periodo)
            if date >= inicio_periodo and fim_agendamento <= fim_periodo:
                horario_valido = True
                break
        if not horario_valido:
            return response(False, "Horário fora do período de atendimento do profissional")

        # 3. Verificar se o horário está livre (não colide com outros agendamentos)
        horarios_ocupados = obter_agendamentos_existentes(db, agendamento.profissional_id, date)
        for ocupado in horarios_ocupados:

            # Se há alguma sobreposição entre o agendamento pretendido e um horário ocupado
            if date < ocupado['fim'] and fim_agendamento > ocupado['inicio']:
                return response(False, "Horário indisponível, já existe agendamento neste período")

        agendamento.start = date
        agendamento.end = fim_agendamento
        db.add(agendamento)
        db.commit()

        # Google Calendar
        gcm = GoogleCalendarManager(profissional.calendar_id, os.environ.get('GOOGLE_CREDENTIAL_JSON_B64'))
        gcm.reschedule_event(
            event_id=agendamento.google_event_id,
            new_start_time=date,
            new_end_time=fim_agendamento,
        )

        return response(True, 'Agendamento reagendado com sucesso', {
            "id": agendamento.id,
            "inicio": agendamento.start.strftime('%Y-%m-%d %H:%M'),
            "fim": agendamento.end.strftime('%Y-%m-%d %H:%M')
        })
    finally:
        db.close()


@agendamentos_router.get('/', name='n8n-agendamentos')
async def get_agendamentos(cliente_id: int, status='agendado', date: str = '0000-00-00'):
    db = SessionLocal()
    date = datetime.strptime(date, '%Y-%m-%d') if date != '0000-00-00' else datetime.now()
    try:
        agendamentos = db.query(Agendamento).filter(
            Agendamento.cliente_id == cliente_id,
            Agendamento.status == status,
            func.date(Agendamento.start) == date
        ).all()
        if not agendamentos:
            return response(False, "Nenhum agendamento encontrado")

        agendamentos_data = []
        for agendamento in agendamentos:
            agendamentos_data.append({
                "id": agendamento.id,
                "inicio": agendamento.start.strftime('%Y-%m-%d %H:%M'),
                "fim": agendamento.end.strftime('%Y-%m-%d %H:%M'),
                "servicos": ", ".join(
                    [servico.name for servico in db.query(Servico).filter(Servico.id.in_(agendamento.servicos)).all()]),
                "profissional": db.query(Profissional).filter(
                    Profissional.id == agendamento.profissional_id).first().name
            })

        return response(True, "Agendamentos encontrados", agendamentos_data)
    finally:
        db.close()


def validar_data(date_str: str) -> Tuple[bool, Any]:
    """Valida e converte a string de data para objeto datetime."""
    try:
        data = datetime.strptime(date_str, '%Y-%m-%d')
        dia_semana = str(data.weekday())
        return True, (data, dia_semana)
    except ValueError:
        return False, "Formato de data inválido, use YYYY-MM-DD"


def verificar_disponibilidade_profissional(
        db, profissional_id: int, servicos_ids: List[int], dia_semana: str
) -> Tuple[bool, Any, Optional[Profissional], Optional[List[Servico]], Optional[int]]:
    """
    Verifica se o profissional está disponível para os serviços no dia da semana.
    Retorna também a duração total dos serviços.
    """
    servicos = []
    duracao_total = 0

    profissional = db.query(Profissional).filter(Profissional.id == profissional_id).first()
    if not profissional:
        return False, "Profissional não encontrado", None, None, None

    # Verificar cada serviço solicitado
    for servico_id in servicos_ids:
        servico = db.query(Servico).filter(Servico.id == servico_id).first()
        if not servico:
            return False, f"Serviço com ID {servico_id} não encontrado", None, None, None

        # Verificar se o profissional atende o serviço
        if servico_id not in profissional.services:
            return False, f"Profissional não atende o serviço: {servico.name}", None, None, None

        servicos.append(servico)
        duracao_total += servico.minutes

    # Verificar se o profissional trabalha neste dia da semana
    horarios_do_dia = profissional.horarios.get(dia_semana, [])
    if not horarios_do_dia:
        return False, "Profissional não atende neste dia da semana", None, None, None

    return True, horarios_do_dia, profissional, servicos, duracao_total


def obter_agendamentos_existentes(db, profissional_id: int, data: datetime) -> List[Dict]:
    """Obtém os agendamentos existentes do profissional na data especificada."""
    inicio_dia = datetime.combine(data, time(0, 0, 0))
    fim_dia = datetime.combine(data, time(23, 59, 59))

    agendamentos = db.query(Agendamento).filter(
        Agendamento.profissional_id == profissional_id,
        Agendamento.start >= inicio_dia,
        Agendamento.end <= fim_dia,
        Agendamento.status != 'cancelado'
    ).all()

    return [{'inicio': a.start, 'fim': a.end} for a in agendamentos]


def gerar_slots_disponiveis(
        data: datetime,
        horarios_do_dia: List[Dict],
        servico_duration: int,
        horarios_ocupados: List[Dict]
) -> List[Dict]:
    """Gera slots disponíveis com base nos horários de trabalho e agendamentos existentes."""
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
                })

            # Avança para o próximo slot
            slot_atual += timedelta(minutes=intervalo_minutos)

    return horarios_disponiveis


def response(success=True, message="", data=None):
    """
    Formata a resposta da API.
    """
    return {
        "success": success,
        "message": message,
        "data": data
    }
