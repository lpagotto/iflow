# app/schemas.py
from pydantic import BaseModel

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
