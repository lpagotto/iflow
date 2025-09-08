# app/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("DATABASE_URL_PRIVATE") or os.getenv("DATABASE_URL_PUBLIC")
if not DATABASE_URL:
    # fallback para desenvolvimento local (opcional)
    DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/postgres"

# IMPORTANTe no Railway/Cloud: pool_pre_ping=True para conexões recicladas
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency usada pelo FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
