from sqlalchemy import Column, Integer, String, DateTime, func

from app.database import Base


class Agendamento(Base):
    __tablename__ = 'agendamentos'
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, nullable=False)
    start = Column(DateTime, nullable=False)
    end = Column(DateTime, nullable=False)
    title = Column(String)
    description = Column(String, default="novo")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())