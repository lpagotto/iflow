from fastapi import FastAPI, Depends, HTTPException, Request, Query
from fastapi.responses import PlainTextResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List

from .db import Base, engine, get_db
from .entities import Patient, Exam
from .schemas import PatientCreate, PatientOut, ExamOut
from .settings import settings
from .whatsapp import (
    send_template_message, send_text, send_document,
    get_media_url, download_media
)
from .storage import upload_bytes
from .processing import process_audio_bytes
from .report import build_pdf_bytes

app = FastAPI(title="UroFlux MVP")

# cria tabelas no startup
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.get("/health")
def health():
    return {"status": "ok"}

# --------- Pacientes ---------
@app.post("/patients", response_model=PatientOut)
def create_patient(p: PatientCreate, db: Session = Depends(get_db)):
    existing = db.query(Patient).filter(
        (Patient.cpf == p.cpf) | (Patient.whatsapp == p.whatsapp)
    ).first()
    if existing:
        raise HTTPException(400, "CPF ou WhatsApp já cadastrado.")
    obj = Patient(name=p.name, cpf=p.cpf, whatsapp=p.whatsapp)
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

@app.get("/patients", response_model=List[PatientOut])
def list_patients(q: Optional[str] = Query(None), db: Session = Depends(get_db)):
    qry = db.query(Patient)
    if q:
        like = f"%{q}%"
        qry = qry.filter((Patient.name.ilike(like)) | (Patient.cpf.ilike(like)) | (Patient.whatsapp.ilike(like)))
    return qry.order_by(Patient.id.desc()).limit(100).all()

@app.get("/patients/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    obj = db.query(Patient).get(patient_id)
    if not obj:
        raise HTTPException(404, "Paciente não encontrado.")
    return obj

# --------- Exams ----------
@app.get("/exams", response_model=List[ExamOut])
def list_exams(patient_id: Optional[int] = None, db: Session = Depends(get_db)):
    qry = db.query(Exam)
    if patient_id:
        qry = qry.filter(Exam.patient_id == patient_id)
    return qry.order_by(Exam.id.desc()).limit(200).all()

@app.get("/exams/{exam_id}", response_model=ExamOut)
def get_exam(exam_id: int, db: Session = Depends(get_db)):
    obj = db.query(Exam).get(exam_id)
    if not obj:
        raise HTTPException(404, "Exame não encontrado.")
    return obj

# --------- Enviar instruções via WhatsApp ----------
@app.post("/send-instructions/{patient_id}")
def send_instructions(patient_id: int, db: Session = Depends(get_db)):
    p = db.query(Patient).get(patient_id)
    if not p:
        raise HTTPException(404, "Paciente não encontrado.")
    # use um template aprovado no Cloud API
    try:
        send_template_message(
            to_whatsapp=p.whatsapp,
            template_name="uroflux_instrucoes_audio",  # ajuste ao seu template
            lang="pt_BR"
        )
    except Exception as e:
        raise HTTPException(500, f"Falha ao enviar WhatsApp: {e}")
    return {"ok": True}

# --------- Webhook do WhatsApp ----------
# Verificação do webhook (GET)
@app.get("/webhook/meta", response_class=PlainTextResponse)
def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        return challenge or ""
    return PlainTextResponse("erro", status_code=403)

# Recebimento de mensagens (POST)
@app.post("/webhook/meta")
def receive_webhook(payload: dict, db: Session = Depends(get_db)):
    try:
        entries = payload.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                messages = value.get("messages", [])
                for msg in messages:
                    msg_id = msg.get("id")
                    from_wa = msg.get("from")  # número do paciente
                    _type = msg.get("type")

                    if _type == "audio":
                        media_id = msg.get("audio", {}).get("id")
                        handle_audio_message(db, from_wa, media_id, msg_id)
                    else:
                        # Responder pedindo áudio
                        send_text(from_wa, "Por favor, envie uma mensagem de *áudio* para realizar o exame.")
        return {"ok": True}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

def handle_audio_message(db: Session, from_whatsapp: str, media_id: str, meta_message_id: str):
    # achar paciente pelo whatsapp
    patient = db.query(Patient).filter(Patient.whatsapp == from_whatsapp).first()
    if not patient:
        # opcional: responder
        send_text(from_whatsapp, "Não encontrei seu cadastro. Peça ao seu médico para cadastrá-lo.")
        return

    # criar exam como "processing"
    exam = Exam(patient_id=patient.id, status="processing", meta_message_id=meta_message_id)
    db.add(exam); db.commit(); db.refresh(exam)

    # baixar áudio da Meta
    media_url = get_media_url(media_id)
    audio_bytes = download_media(media_url)

    # (opcional) subir áudio bruto em storage
    audio_key = f"audios/patient_{patient.id}_exam_{exam.id}.ogg"
    audio_url = upload_bytes(audio_key, audio_bytes, content_type="audio/ogg")
    exam.audio_url = audio_url
    db.commit()

    # processar (rodar seu modelo)
    try:
        metrics = process_audio_bytes(audio_bytes)
        pdf_bytes = build_pdf_bytes(patient.name, patient.cpf, metrics)

        pdf_key = f"reports/patient_{patient.id}_exam_{exam.id}.pdf"
        pdf_url = upload_bytes(pdf_key, pdf_bytes, content_type="application/pdf")
        exam.pdf_url = pdf_url
        exam.status = "done"
        db.commit()

        # enviar PDF ao paciente
        send_document(to_whatsapp=from_whatsapp, doc_url=pdf_url, caption="Seu resultado UroFlux")

    except Exception as e:
        exam.status = "failed"
        db.commit()
        send_text(from_whatsapp, "Houve um problema ao processar seu exame. Tente novamente mais tarde.")
        raise
