from sqlalchemy import Column, Integer, String, DateTime, func, JSON
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class Agendamento(Base):
    __tablename__ = 'agendamentos'
    id = Column(Integer, primary_key=True, index=True)
    servicos = Column(JSON, nullable=False)
    cliente_id = Column(Integer, nullable=False)
    profissional_id = Column(Integer, nullable=False)
    start = Column(DateTime, nullable=False)
    end = Column(DateTime, nullable=False)
    title = Column(String)
    description = Column(String)
    status = Column(String, nullable=False, default='agendado')
    google_event_id = Column(String, nullable=True)
    client_metadata = Column(JSONB, nullable=True, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())