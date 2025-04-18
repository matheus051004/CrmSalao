from pydantic import BaseModel


class ServicoAdd(BaseModel):
    servico: str
    descricao: str
    preco: float
    minutos: int
    sexo: str