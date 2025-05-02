from pydantic import BaseModel


class ProfissionalAdd(BaseModel):
    nome: str
    calendar_id: str
    servicos: list[int]
    horarios: dict[str, list]