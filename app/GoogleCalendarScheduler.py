import os
import datetime
from typing import List, Tuple, Dict, Optional, Union
from datetime import datetime, timedelta, time

from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle


class GoogleCalendarSchedulerVPS:
    """
    Versão da classe GoogleCalendarScheduler para uso em ambientes headless como VPS,
    utilizando uma Service Account para autenticação.
    """

    def __init__(self,
                 service_account_file: str,
                 calendar_id: str,  # Este deve ser o e-mail da conta de calendário que você deseja acessar
                 horarios_funcionamento: Dict[int, List[Dict[str, str]]] = None,
                 timezone: str = 'America/Sao_Paulo'):
        """
        Inicializa o gerenciador de agenda do Google Calendar.

        Args:
            service_account_file: Arquivo JSON com as credenciais da Service Account
            calendar_id: ID do calendário a ser utilizado (e-mail do calendário)
            horarios_funcionamento: Dicionário com os horários de funcionamento para cada dia da semana
            timezone: Fuso horário do estabelecimento
        """
        self.calendar_id = calendar_id
        self.timezone = timezone

        # Configuração padrão de horários se nenhuma for fornecida
        if not horarios_funcionamento:
            self.horarios_funcionamento = {
                0: [{"inicio": "09:00", "fim": "12:00"}, {"inicio": "13:00", "fim": "18:00"}],  # Segunda
                1: [{"inicio": "09:00", "fim": "12:00"}, {"inicio": "13:00", "fim": "18:00"}],  # Terça
                2: [{"inicio": "09:00", "fim": "12:00"}, {"inicio": "13:00", "fim": "18:00"}],  # Quarta
                3: [{"inicio": "09:00", "fim": "12:00"}, {"inicio": "13:00", "fim": "18:00"}],  # Quinta
                4: [{"inicio": "09:00", "fim": "12:00"}, {"inicio": "13:00", "fim": "18:00"}],  # Sexta
                5: [{"inicio": "09:00", "fim": "13:00"}],  # Sábado
                6: []  # Domingo - fechado
            }
        else:
            self.horarios_funcionamento = horarios_funcionamento

        self.service = self._get_calendar_service(service_account_file)

    def _get_calendar_service(self, service_account_file):
        """
        Configura e autentica o serviço do Google Calendar usando Service Account.

        Args:
            service_account_file: Caminho para o arquivo JSON da Service Account

        Returns:
            Serviço autenticado do Google Calendar
        """
        SCOPES = ['https://www.googleapis.com/auth/calendar']

        credentials = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=SCOPES)

        # Constrói e retorna o serviço
        return build('calendar', 'v3', credentials=credentials)

    def _convert_to_datetime(self, data: str, hora: str) -> datetime:
        """
        Converte uma string de data e hora para um objeto datetime.

        Args:
            data: Data no formato 'YYYY-MM-DD'
            hora: Hora no formato 'HH:MM'

        Returns:
            Objeto datetime
        """
        data_hora_str = f"{data}T{hora}:00"
        return datetime.fromisoformat(data_hora_str)

    def _esta_em_horario_funcionamento(self, data_hora: datetime) -> bool:
        """
        Verifica se uma data e hora estão dentro do horário de funcionamento.

        Args:
            data_hora: Data e hora a serem verificadas

        Returns:
            True se estiver dentro do horário de funcionamento, False caso contrário
        """
        dia_semana = data_hora.weekday()  # 0 = segunda, 6 = domingo

        # Verifica se há horários de funcionamento definidos para este dia
        if dia_semana not in self.horarios_funcionamento or not self.horarios_funcionamento[dia_semana]:
            return False

        # Verifica se a hora está dentro de algum dos períodos de funcionamento do dia
        hora_atual = data_hora.time()

        for periodo in self.horarios_funcionamento[dia_semana]:
            hora_inicio = datetime.strptime(periodo["inicio"], "%H:%M").time()
            hora_fim = datetime.strptime(periodo["fim"], "%H:%M").time()

            if hora_inicio <= hora_atual < hora_fim:
                return True

        return False

    def _get_periodos_funcionamento_data(self, data: str) -> List[Tuple[datetime, datetime]]:
        """
        Retorna os períodos de funcionamento para uma data específica.

        Args:
            data: Data no formato 'YYYY-MM-DD'

        Returns:
            Lista de tuplas com os horários de início e fim de cada período
        """
        data_obj = datetime.fromisoformat(f"{data}T00:00:00")
        dia_semana = data_obj.weekday()

        periodos = []

        # Verifica se há horários de funcionamento definidos para este dia
        if dia_semana in self.horarios_funcionamento and self.horarios_funcionamento[dia_semana]:
            for periodo in self.horarios_funcionamento[dia_semana]:
                inicio = self._convert_to_datetime(data, periodo["inicio"])
                fim = self._convert_to_datetime(data, periodo["fim"])
                periodos.append((inicio, fim))

        return periodos

    def verificar_horario_livre(self, data: str, hora: str, duracao_minutos: int) -> bool:
        """
        Verifica se um horário específico está livre para um serviço de duração específica.

        Args:
            data: Data no formato 'YYYY-MM-DD'
            hora: Hora no formato 'HH:MM'
            duracao_minutos: Duração do serviço em minutos

        Returns:
            True se o horário estiver livre, False caso contrário
        """
        inicio = self._convert_to_datetime(data, hora)
        fim = inicio + timedelta(minutes=duracao_minutos)

        # Verifica se o horário inicial está dentro do período de funcionamento
        if not self._esta_em_horario_funcionamento(inicio):
            return False

        # Verifica se o horário final está dentro do período de funcionamento
        # Subtrai 1 minuto para garantir que o fim do serviço ainda esteja dentro do horário
        if not self._esta_em_horario_funcionamento(fim - timedelta(minutes=1)):
            return False

        # Verifica se o serviço não ultrapassa um período de funcionamento para outro (como o intervalo de almoço)
        periodos = self._get_periodos_funcionamento_data(data)
        esta_em_periodo_continuo = False

        for periodo_inicio, periodo_fim in periodos:
            if periodo_inicio <= inicio and fim <= periodo_fim:
                esta_em_periodo_continuo = True
                break

        if not esta_em_periodo_continuo:
            return False

        # Define o intervalo de tempo para verificar eventos
        time_min = inicio.isoformat() + 'Z'  # 'Z' indica UTC
        time_max = fim.isoformat() + 'Z'

        # Busca eventos no intervalo
        eventos = self.service.events().list(
            calendarId=self.calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        # Se há eventos, o horário não está livre
        return len(eventos.get('items', [])) == 0

    def obter_horarios_livres(self, data: str, duracao_minutos: int) -> List[str]:
        """
        Obtém uma lista de horários livres em um dia para um serviço de duração específica.

        Args:
            data: Data no formato 'YYYY-MM-DD'
            duracao_minutos: Duração do serviço em minutos

        Returns:
            Lista de horários livres no formato 'HH:MM'
        """
        # Verifica se há períodos de funcionamento para este dia
        periodos = self._get_periodos_funcionamento_data(data)
        if not periodos:
            return []

        # Data base para buscar eventos
        data_base = datetime.fromisoformat(f"{data}T00:00:00")

        # Define os limites de início e fim do dia para buscar todos os eventos
        inicio_dia = data_base
        fim_dia = data_base + timedelta(days=1)

        # Busca eventos do dia
        time_min = inicio_dia.isoformat() + 'Z'
        time_max = fim_dia.isoformat() + 'Z'

        eventos = self.service.events().list(
            calendarId=self.calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        # Lista de eventos do dia
        eventos_dia = eventos.get('items', [])

        # Intervalo de verificação em minutos (divisão do dia)
        intervalo = 15  # Verifica a cada 15 minutos

        # Lista para armazenar horários livres
        horarios_livres = []

        # Para cada período de funcionamento, verifica os horários livres
        for periodo_inicio, periodo_fim in periodos:
            # Ajusta o período de fim para garantir que o serviço completo caiba dentro do período
            periodo_fim_ajustado = periodo_fim - timedelta(minutes=duracao_minutos - 1)

            # Se o período ajustado é inválido (duração maior que o período), continua
            if periodo_fim_ajustado <= periodo_inicio:
                continue

            # Verifica cada intervalo dentro do período de funcionamento
            atual = periodo_inicio
            while atual <= periodo_fim_ajustado:
                fim_atual = atual + timedelta(minutes=duracao_minutos)

                # Verifica conflitos com eventos existentes
                tem_conflito = False
                for evento in eventos_dia:
                    # Pula eventos que não têm dateTime definido (eventos de dia inteiro)
                    if 'dateTime' not in evento['start'] or 'dateTime' not in evento['end']:
                        continue

                    inicio_evento = datetime.fromisoformat(evento['start'].get('dateTime', '').replace('Z', '+00:00'))
                    fim_evento = datetime.fromisoformat(evento['end'].get('dateTime', '').replace('Z', '+00:00'))

                    # Verifica se há sobreposição
                    if (atual < fim_evento and fim_atual > inicio_evento):
                        tem_conflito = True
                        break

                # Se não houver conflito, adiciona à lista de horários livres
                if not tem_conflito:
                    horarios_livres.append(atual.strftime('%H:%M'))

                # Avança para o próximo intervalo
                atual += timedelta(minutes=intervalo)

        return horarios_livres

    def agendar_servico(self, data: str, hora: str, duracao_minutos: int,
                        titulo: str, descricao: str = "",
                        cliente: Dict = None) -> Optional[str]:
        """
        Agenda um serviço no calendário.

        Args:
            data: Data no formato 'YYYY-MM-DD'
            hora: Hora no formato 'HH:MM'
            duracao_minutos: Duração do serviço em minutos
            titulo: Título do evento
            descricao: Descrição do evento
            cliente: Dicionário com informações do cliente

        Returns:
            ID do evento criado ou None se não foi possível agendar
        """
        # Verifica se o horário está livre
        if not self.verificar_horario_livre(data, hora, duracao_minutos):
            return None

        # Define o início e fim do evento
        inicio = self._convert_to_datetime(data, hora)
        fim = inicio + timedelta(minutes=duracao_minutos)

        # Cria o evento
        event = {
            'summary': titulo,
            'description': descricao,
            'start': {
                'dateTime': inicio.isoformat(),
                'timeZone': self.timezone,
            },
            'end': {
                'dateTime': fim.isoformat(),
                'timeZone': self.timezone,
            },
        }

        # Adiciona informações do cliente se fornecidas
        if cliente:
            event['extendedProperties'] = {
                'private': {
                    'cliente': str(cliente),
                    'duracao_minutos': str(duracao_minutos)
                }
            }

        # Cria o evento no calendário
        evento_criado = self.service.events().insert(calendarId=self.calendar_id, body=event).execute()
        return evento_criado.get('id')

    def reagendar_servico(self, event_id: str, nova_data: str, nova_hora: str) -> bool:
        """
        Reagenda um serviço existente para uma nova data e hora.

        Args:
            event_id: ID do evento a ser reagendado
            nova_data: Nova data no formato 'YYYY-MM-DD'
            nova_hora: Nova hora no formato 'HH:MM'

        Returns:
            True se o reagendamento foi bem-sucedido, False caso contrário
        """
        try:
            # Busca o evento original
            evento = self.service.events().get(calendarId=self.calendar_id, eventId=event_id).execute()

            # Obtém a duração original do evento
            # Primeiro tenta obter do extended properties, se não conseguir, calcula da diferença entre início e fim
            duracao_minutos = None
            if 'extendedProperties' in evento and 'private' in evento['extendedProperties']:
                duracao_minutos = evento['extendedProperties']['private'].get('duracao_minutos')

            if not duracao_minutos:
                inicio_evento = datetime.fromisoformat(evento['start'].get('dateTime', '').replace('Z', '+00:00'))
                fim_evento = datetime.fromisoformat(evento['end'].get('dateTime', '').replace('Z', '+00:00'))
                duracao_minutos = int((fim_evento - inicio_evento).total_seconds() / 60)
            else:
                duracao_minutos = int(duracao_minutos)

            # Verifica se o novo horário está livre
            if not self.verificar_horario_livre(nova_data, nova_hora, duracao_minutos):
                return False

            # Define o novo início e fim do evento
            novo_inicio = self._convert_to_datetime(nova_data, nova_hora)
            novo_fim = novo_inicio + timedelta(minutes=duracao_minutos)

            # Atualiza os horários do evento
            evento['start']['dateTime'] = novo_inicio.isoformat()
            evento['end']['dateTime'] = novo_fim.isoformat()

            # Atualiza o evento no calendário
            self.service.events().update(calendarId=self.calendar_id, eventId=event_id, body=evento).execute()
            return True
        except Exception as e:
            print(f"Erro ao reagendar serviço: {e}")
            return False

    def cancelar_agendamento(self, event_id: str) -> bool:
        """
        Cancela um agendamento existente.

        Args:
            event_id: ID do evento a ser cancelado

        Returns:
            True se o cancelamento foi bem-sucedido, False caso contrário
        """
        try:
            self.service.events().delete(calendarId=self.calendar_id, eventId=event_id).execute()
            return True
        except Exception as e:
            print(f"Erro ao cancelar agendamento: {e}")
            return False

    def listar_agendamentos(self, data_inicio: str, data_fim: str = None) -> List[Dict]:
        """
        Lista todos os agendamentos em um intervalo de datas.

        Args:
            data_inicio: Data inicial no formato 'YYYY-MM-DD'
            data_fim: Data final no formato 'YYYY-MM-DD' (opcional, padrão é a mesma data de início)

        Returns:
            Lista de agendamentos
        """
        if not data_fim:
            data_fim = data_inicio

        # Converte para datetime
        inicio = datetime.fromisoformat(f"{data_inicio}T00:00:00")
        fim = datetime.fromisoformat(f"{data_fim}T23:59:59")

        # Define o intervalo de tempo para busca
        time_min = inicio.isoformat() + 'Z'
        time_max = fim.isoformat() + 'Z'

        # Busca eventos no intervalo
        eventos = self.service.events().list(
            calendarId=self.calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        # Formata os resultados
        resultados = []
        for evento in eventos.get('items', []):
            # Pula eventos que não têm dateTime definido (eventos de dia inteiro)
            if 'dateTime' not in evento['start'] or 'dateTime' not in evento['end']:
                continue

            inicio_evento = datetime.fromisoformat(evento['start'].get('dateTime', '').replace('Z', '+00:00'))
            fim_evento = datetime.fromisoformat(evento['end'].get('dateTime', '').replace('Z', '+00:00'))

            resultados.append({
                'id': evento['id'],
                'titulo': evento.get('summary', ''),
                'descricao': evento.get('description', ''),
                'inicio': inicio_evento.strftime('%Y-%m-%d %H:%M'),
                'fim': fim_evento.strftime('%Y-%m-%d %H:%M'),
                'duracao_minutos': int((fim_evento - inicio_evento).total_seconds() / 60),
                'cliente': evento.get('extendedProperties', {}).get('private', {}).get('cliente', '')
            })

        return resultados

    def alterar_horario_funcionamento(self, dia_semana: int, periodos: List[Dict[str, str]]) -> None:
        """
        Altera o horário de funcionamento para um dia específico da semana.

        Args:
            dia_semana: Dia da semana (0 = segunda, 6 = domingo)
            periodos: Lista de períodos de funcionamento no formato [{"inicio": "HH:MM", "fim": "HH:MM"}, ...]
        """
        if dia_semana < 0 or dia_semana > 6:
            raise ValueError("O dia da semana deve estar entre 0 (segunda) e 6 (domingo)")

        # Valida os períodos
        for periodo in periodos:
            if "inicio" not in periodo or "fim" not in periodo:
                raise ValueError("Cada período deve ter as chaves 'inicio' e 'fim'")

            try:
                datetime.strptime(periodo["inicio"], "%H:%M")
                datetime.strptime(periodo["fim"], "%H:%M")
            except ValueError:
                raise ValueError("O formato de hora deve ser 'HH:MM'")

            if periodo["inicio"] >= periodo["fim"]:
                raise ValueError("A hora de início deve ser anterior à hora de fim")

        # Ordena os períodos por hora de início
        periodos_ordenados = sorted(periodos, key=lambda x: x["inicio"])

        # Verifica sobreposição de períodos
        for i in range(len(periodos_ordenados) - 1):
            if periodos_ordenados[i]["fim"] > periodos_ordenados[i + 1]["inicio"]:
                raise ValueError("Os períodos não podem se sobrepor")

        # Atualiza o horário de funcionamento
        self.horarios_funcionamento[dia_semana] = periodos_ordenados
