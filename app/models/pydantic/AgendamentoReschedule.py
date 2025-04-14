from pydantic import BaseModel


class AgendamentoReschedule(BaseModel):
    cliente_id: int
    agendamento_id: int
    new_date_time: str