from pydantic import BaseModel
from typing import Optional

class BrightnessModel(BaseModel):
    brightness: int

class ArtistVisualModel(BaseModel):
    media: str  # ou artist_id si tu préfères un identifiant

class QRCodeModel(BaseModel):
    url: str

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
