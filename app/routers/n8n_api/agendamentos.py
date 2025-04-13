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
async def horarios_diponiveis(date: str, profissional_id: int, servicos_ids: List[int]):
    """Retorna os horários disponíveis para agendamentos de múltiplos serviços."""
    # Validar a data
    sucesso, resultado = validar_data(date)
    if not sucesso:
        return response(False, resultado)

    data, dia_semana = resultado

    db = SessionLocal()
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
    title = dados.title
    description = dados.description

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
        titulo_auto = f"Agendamento de {nomes_servicos}"

        # Criar o agendamento
        novo_agendamento = Agendamento(
            cliente_id=cliente_id,
            profissional_id=profissional_id,
            servicos=servicos_ids,
            start=inicio_agendamento,
            end=fim_agendamento,
            title=title if title else titulo_auto,
            description=description,
            status="agendado"
        )

        db.add(novo_agendamento)
        db.commit()
        db.refresh(novo_agendamento)

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
