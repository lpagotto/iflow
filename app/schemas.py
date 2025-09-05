from pydantic import BaseModel, Field

class PatientCreate(BaseModel):
    name: str
    cpf: str
    whatsapp: str

class PatientOut(BaseModel):
    id: int
    name: str
    cpf: str
    whatsapp: str
    class Config:
        from_attributes = True

class ExamOut(BaseModel):
    id: int
    patient_id: int
    status: str
    audio_url: str | None = None
    pdf_url: str | None = None
    class Config:
        from_attributes = True
