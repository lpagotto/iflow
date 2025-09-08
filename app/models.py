# app/models.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    cpf = Column(String, unique=True, index=True, nullable=False)
    whatsapp = Column(String, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Exam(Base):
    __tablename__ = "exams"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    status = Column(String, default="pending", index=True)
    audio_s3_key = Column(String, nullable=True)    # onde o áudio foi salvo
    pdf_s3_key = Column(String, nullable=True)      # laudo PDF
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient")
