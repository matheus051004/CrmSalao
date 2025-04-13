from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


def default_horarios():
    return {
        "0": [
            {
                "fim": "12:00",
                "inicio": "09:00"
            },
            {
                "fim": "18:00",
                "inicio": "13:00"
            }
        ],
        "1": [
            {
                "fim": "12:00",
                "inicio": "09:00"
            },
            {
                "fim": "18:00",
                "inicio": "13:00"
            }
        ],
        "2": [
            {
                "fim": "12:00",
                "inicio": "09:00"
            },
            {
                "fim": "18:00",
                "inicio": "13:00"
            }
        ],
        "3": [
            {
                "fim": "12:00",
                "inicio": "09:00"
            },
            {
                "fim": "18:00",
                "inicio": "13:00"
            }
        ],
        "4": [
            {
                "fim": "12:00",
                "inicio": "09:00"
            },
            {
                "fim": "18:00",
                "inicio": "13:00"
            }
        ],
        "5": [
            {
                "fim": "13:00",
                "inicio": "09:00"
            }
        ],
        "6": []
    }


class Profissional(Base):
    __tablename__ = 'profissionais'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    calendar_id = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    services = Column(JSONB, default=[])
    sexo = Column(String, nullable=False, default='masculino')
    horarios = Column(JSONB, default=default_horarios())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
