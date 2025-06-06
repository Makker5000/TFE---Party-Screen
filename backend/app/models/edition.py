from pydantic import BaseModel
from typing import Optional
from app.db import Base
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from typing import Optional

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
    url: Optional[str] = None
    id: Optional[int] = None
    state: Optional[str] = None

    class Config:
        extra = "ignore"

class QrcodeDB(Base):
    __tablename__ = "qrcodes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    preset_id = Column(Integer, ForeignKey("presets.id", ondelete="CASCADE"), nullable=True)
    url = Column(String(2048), nullable=False, index=True)
    data_base64 = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations ORM
    user = relationship("User", back_populates="qrcodes")
    preset = relationship("Preset", back_populates="qrcodes")

class LyricsModel(BaseModel):
    textColor: str
    backgroundColor: str
    font: str
    animation: str
    state: Optional[str] = None

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
