from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from app.db import Base

class PowerModel(BaseModel):
    power: bool

class SettingsModel(BaseModel):
    screenCount: int
    matrixCount: int
    screenShape: str

class SettingsDB(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True)
    screen_count = Column(Integer, nullable=False)
    matrix_count = Column(Integer, nullable=False)
    screen_shape = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
