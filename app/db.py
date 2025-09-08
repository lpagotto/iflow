# app/db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = os.getenv("DATABASE_URL")  # no Railway: já vem setado

# --- Base declarativa (SQLAlchemy 2.0) ---
class Base(DeclarativeBase):
    pass

# --- Engine & Session ---
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# --- Dependency do FastAPI ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
