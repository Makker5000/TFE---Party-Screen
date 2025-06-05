# app/db.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()  # lit ton .env

DATABASE_URL = os.getenv("DATABASE_URL")
# Exemple : mysql+aiomysql://devuser:devpass@127.0.0.1:3306/myapp_dev

# engine = create_async_engine(
#     DATABASE_URL,
#     echo=True,           # passe à False en prod
#     future=True
# )

# AsyncSessionLocal = sessionmaker(
#     engine, 
#     class_=AsyncSession,
#     expire_on_commit=False,
# )

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    # (pas besoin de connect_args pour MySQL/MariaDB)
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

# Fonction pour accéder à la DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()