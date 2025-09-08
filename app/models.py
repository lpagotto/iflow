from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .db import Base

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    cpf = Column(String, unique=True, index=True, nullable=False)
    whatsapp = Column(String, index=True, nullable=False)

class Exam(Base):
    __tablename__ = "exams"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    status = Column(String, default="pending")
    s3_key = Column(String)        # caminho do áudio/processado
    pdf_s3_key = Column(String)    # caminho do laudo PDF
    patient = relationship("Patient")
