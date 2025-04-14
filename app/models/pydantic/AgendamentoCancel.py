from typing import Optional, List

from pydantic import BaseModel

from typing import Optional, List
from pydantic import BaseModel


class AgendamentoCancel(BaseModel):
    """
    Modelo Pydantic para representar o cancelamento de um agendamento.

    Atributos:
        cliente_id (int): Identificador único do cliente associado ao agendamento.
        agendamento_id (int): Identificador único do agendamento a ser cancelado.
    """
    cliente_id: int
    agendamento_id: int
