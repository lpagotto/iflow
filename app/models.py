# app/models.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .db import Base
from datetime import datetime

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    cpf = Column(String(14), unique=True, index=True, nullable=False)
    whatsapp = Column(String(32), index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    exams = relationship("Exam", back_populates="patient")

class Exam(Base):
    __tablename__ = "exams"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)

    # novos campos para casar com o main.py
    meta_message_id = Column(String(64), nullable=True)  # id da mensagem do WhatsApp
    audio_url = Column(Text, nullable=True)              # onde guardamos o áudio
    pdf_url = Column(Text, nullable=True)                # onde guardamos o PDF

    status = Column(String(32), default="received", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    patient = relationship("Patient", back_populates="exams")
