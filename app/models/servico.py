from sqlalchemy import Column, Integer, String, DateTime, func, DECIMAL

from app.database import Base


class Servico(Base):
    __tablename__ = 'servicos'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price = Column(DECIMAL, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())