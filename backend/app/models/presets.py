# app/models/preset.py
from sqlalchemy import Column, Integer, String, JSON, TIMESTAMP, func, ForeignKey
from app.db import Base
from pydantic import BaseModel
from sqlalchemy.orm import relationship

# --- Schémas Pydantic ---
class PresetCreate(BaseModel):
    name: str
    type: str
    data: dict

class PresetRead(PresetCreate):
    id: int

class Preset(Base):
    __tablename__ = "presets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
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

    # Relation bidirectionnelle vers VisualDB
    visuals = relationship("ArtistVisualDB", back_populates="preset", cascade="all, delete-orphan")
    # Relation vers QrcodeDB
    qrcodes = relationship("QrcodeDB", back_populates="preset", cascade="all, delete-orphan")
    # Relation avec User
    user = relationship("User", back_populates="presets")
