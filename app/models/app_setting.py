from sqlalchemy import Column, Integer, String, DateTime, func, DECIMAL

from app.database import Base


class AppSetting(Base):
    __tablename__ = 'app_settings'
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(30), unique=True, index=True)
    value = Column(String(255))