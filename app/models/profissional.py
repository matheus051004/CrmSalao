from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class Profissional(Base):
    __tablename__ = 'profissionais'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    calendar_id = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    areas = Column(String, default='')
    services = Column(JSONB, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())