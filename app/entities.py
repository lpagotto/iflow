from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .db import Base

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    cpf = Column(String(32), nullable=False, index=True)
    whatsapp = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    exams = relationship("Exam", back_populates="patient")

class Exam(Base):
    __tablename__ = "exams"
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    audio_url = Column(Text)
    pdf_url = Column(Text)
    status = Column(String(32), default="received")  # received|processing|done|failed
    meta_message_id = Column(String(128), index=True, nullable=True)  # id da mensagem no WhatsApp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    patient = relationship("Patient", back_populates="exams")
