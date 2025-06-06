from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.db import Base
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relation vers Preset et Qrcode
    presets = relationship("Preset", back_populates="user", cascade="all, delete-orphan")
    qrcodes = relationship("QrcodeDB", back_populates="user", cascade="all, delete-orphan")

# --- Pydantic schemas ---
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UpdateUsername(BaseModel):
    new_username: str

class UpdatePassword(BaseModel):
    current_password: str
    new_password: str

class LoginUser(BaseModel):
    email: EmailStr
    password: str