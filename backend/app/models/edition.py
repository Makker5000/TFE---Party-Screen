from pydantic import BaseModel
from typing import Optional
from app.db import Base
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

class BrightnessModel(BaseModel):
    brightness: int

class ArtistVisualModel(BaseModel):
    # media: str  # ou artist_id si tu préfères un identifiant
    media: dict

class ArtistVisualDB(Base):
    __tablename__ = "visuals"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), unique=True, index=True, nullable=False)
    data_base64 = Column(Text, nullable=False)

    # ↑ Nouvel attribut preset_id, clé étrangère vers presets.id
    preset_id = Column(Integer, ForeignKey("presets.id", ondelete="CASCADE"), nullable=True)

    # Relation bidirectionnelle (facultative) :
    # permet d’accéder à visual.preset si vous l’utilisez dans ORM
    preset = relationship("Preset", back_populates="visuals")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class QRCodeModel(BaseModel):
    url: str

class QRCodePlayModel(BaseModel):
    filename: str

class LyricsModel(BaseModel):
    textColor: str
    backgroundColor: str
    font: str
    animation: str

class AdsModel(BaseModel):
    textColor: str
    backgroundColor: str
    font: str
    animation: str
    speed: int
    content: str
    state: str

# class SongRequest(BaseModel):
#     title: str
#     artist: str
