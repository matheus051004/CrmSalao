from datetime import datetime, time, timedelta
from typing import Tuple, Any, Optional, List, Dict

from fastapi.routing import APIRouter

from app import Servico, Profissional
from app.database import SessionLocal
from app.models.agendamentos import Agendamento
from app.models.pydantic.AgendamentoCreate import AgendamentoCreate

agendamentos_router = APIRouter(
    prefix="/agendamentos",
    include_in_schema=True,
)


@agendamentos_router.get("/horarios-diponiveis", name="n8n-horarios-diponiveis")
async def horarios_diponiveis(date: str, profissional_id: int, servico_id: int):
    """Retorna os horários disponíveis para agendamentos de um serviço."""
    # Validar a data
    sucesso, resultado = validar_data(date)
    if not sucesso:
        return response(False, resultado)

    data, dia_semana = resultado

    db = SessionLocal()
    try:
        # Verificar disponibilidade do profissional
        sucesso, resultado, profissional, servico = verificar_disponibilidade_profissional(
            db, profissional_id, servico_id, dia_semana
        )
        if not sucesso:
            return response(False, resultado)

        horarios_do_dia = resultado
        servico_duration = servico.minutes

        # Obter agendamentos existentes
        horarios_ocupados = obter_agendamentos_existentes(db, profissional_id, data)

        # Gerar slots disponíveis
        horarios_disponiveis = gerar_slots_disponiveis(
            data, horarios_do_dia, servico_duration, horarios_ocupados
        )

        return response(True, "Horários disponíveis", horarios_disponiveis)
    finally:
        db.close()


@agendamentos_router.post("/criar", name="n8n-criar-agendamento")
async def criar_agendamento(dados: AgendamentoCreate):

    cliente_id = dados.cliente_id
    profissional_id = dados.profissional_id
    servico_id = dados.servico_id
    date = dados.date
    start_hour = dados.start_hour
    title = dados.title
    description = dados.description

    # Validar a data
    sucesso, resultado = validar_data(date)
    if not sucesso:
        return response(False, resultado)

    data_obj, dia_semana = resultado

    db = SessionLocal()
    try:
        # 1. Verificar se o profissional atende aquele serviço e trabalha naquele dia
        sucesso, resultado, profissional, servico = verificar_disponibilidade_profissional(
            db, profissional_id, servico_id, dia_semana
        )
        if not sucesso:
            return response(False, resultado)

        horarios_do_dia = resultado
        duracao_servico = servico.minutes

        # 2. Verificar se o horário escolhido está dentro do período de trabalho do profissional
        try:
            hora_inicio = datetime.strptime(start_hour, '%H:%M').time()
            inicio_agendamento = datetime.combine(data_obj, hora_inicio)
            fim_agendamento = inicio_agendamento + timedelta(minutes=duracao_servico)
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

        # Criar o agendamento
        novo_agendamento = Agendamento(
            cliente_id=cliente_id,
            profissional_id=profissional_id,
            servicos=[servico_id],
            start=inicio_agendamento,
            end=fim_agendamento,
            title=title if title else f"Agendamento de {servico.name}",
            description=description,
            status="agendado"
        )

        db.add(novo_agendamento)
        db.commit()
        db.refresh(novo_agendamento)

        # Se o profissional tiver um calendar_id, pode-se integrar com Google Calendar
        # if profissional.calendar_id:
        #     try:
        #         from app.GoogleCalendarManager import GoogleCalendarManager
        #
        #         # Criar evento no Google Calendar
        #         calendar = GoogleCalendarManager(
        #             credentials_path='',
        #             calendar_id=profissional.calendar_id
        #         )
        #
        #         summary = novo_agendamento.title
        #         event = calendar.create_event(
        #             summary=summary,
        #             start_time=novo_agendamento.start,
        #             end_time=novo_agendamento.end,
        #             description=novo_agendamento.description
        #         )
        #
        #         # Opcionalmente, poderia salvar o ID do evento do Google Calendar no agendamento
        #         if event and 'id' in event:
        #             novo_agendamento.google_event_id = event['id']
        #             db.commit()
        #
        #     except Exception as e:
        #         # Não interromper o fluxo se falhar a integração com o Calendar
        #         print(f"Erro ao integrar com Google Calendar: {str(e)}")

        return response(
            True,
            "Agendamento criado com sucesso",
            {
                "id": novo_agendamento.id,
                "inicio": novo_agendamento.start.strftime('%Y-%m-%d %H:%M'),
                "fim": novo_agendamento.end.strftime('%Y-%m-%d %H:%M'),
                "servico": servico.name,
                "profissional": profissional.name
            }
        )

    except Exception as e:
        db.rollback()
        return response(False, f"Erro ao criar agendamento: {str(e)}")
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
        db, profissional_id: int, servico_id: int, dia_semana: str
) -> Tuple[bool, Any, Optional[Profissional], Optional[Servico]]:
    """Verifica se o profissional está disponível para o serviço no dia da semana."""
    servico = db.query(Servico).filter(Servico.id == servico_id).first()
    if not servico:
        return False, "Serviço não encontrado", None, None

    profissional = db.query(Profissional).filter(Profissional.id == profissional_id).first()
    if not profissional:
        return False, "Profissional não encontrado", None, None

    # verificar se o profissional atende o serviço
    if servico_id not in profissional.services:
        return False, "Profissional não atende este serviço", None, None

    # Verificar se o profissional trabalha neste dia da semana
    horarios_do_dia = profissional.horarios.get(dia_semana, [])
    if not horarios_do_dia:
        return False, "Profissional não atende neste dia da semana", None, None

    return True, horarios_do_dia, profissional, servico


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
