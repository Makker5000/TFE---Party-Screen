# app/models/preset.py
from sqlalchemy import Column, Integer, String, JSON, TIMESTAMP, func
from app.db import Base

class Preset(Base):
    __tablename__ = "presets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    data = Column(JSON, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
