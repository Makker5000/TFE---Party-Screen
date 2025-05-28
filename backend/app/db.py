# app/db.py
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()  # lit ton .env

DATABASE_URL = os.getenv("DATABASE_URL")
# Exemple : mysql+aiomysql://devuser:devpass@127.0.0.1:3306/myapp_dev

engine = create_async_engine(
    DATABASE_URL,
    echo=True,           # passe à False en prod
    future=True
)

AsyncSessionLocal = sessionmaker(
    engine, 
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()
