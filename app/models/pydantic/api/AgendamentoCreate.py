from typing import Optional, List

from pydantic import BaseModel


class AgendamentoCreate(BaseModel):
    cliente_id: int
    profissional_id: int
    servicos_ids: List[int]  # Agora aceita uma lista de serviços
    date: str
    start_hour: str
    metadata: Optional[dict[str, str]] = None