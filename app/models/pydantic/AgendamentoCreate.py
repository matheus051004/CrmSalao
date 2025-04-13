from typing import Optional

from pydantic import BaseModel


class AgendamentoCreate(BaseModel):
    cliente_id: int
    profissional_id: int
    servico_id: int
    date: str
    start_hour: str
    title: Optional[str] = None
    description: Optional[str] = None