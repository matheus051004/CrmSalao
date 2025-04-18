from pydantic import BaseModel


class ServicoDelete(BaseModel):
    servico_id: int