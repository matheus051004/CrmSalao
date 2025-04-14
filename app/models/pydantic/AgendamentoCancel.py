from pydantic import BaseModel


class AgendamentoCancel(BaseModel):
    cliente_id: int
    agendamento_id: int