from pydantic import BaseModel


class AgendamentoComplete(BaseModel):
    agendamento_id: int
    notify_cliente: bool
    message: str