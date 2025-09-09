# app/schemas.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

# ---------- Pacientes ----------
class PatientCreate(BaseModel):
    name: str
    cpf: str
    whatsapp: str

class PatientOut(BaseModel):
    id: int
    name: str
    cpf: str
    whatsapp: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ---------- Exames / Resultados ----------
class ExamResultOut(BaseModel):
    id: int
    exam_id: int
    summary: Optional[str] = None
    pdf_url: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ExamOut(BaseModel):
    id: int
    patient_id: int
    audio_url: Optional[str] = None
    status: str
    created_at: datetime
    # pode vir nulo (ainda processando)
    result: Optional[ExamResultOut] = None

    model_config = ConfigDict(from_attributes=True)
