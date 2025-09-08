# app/main.py
from fastapi import FastAPI, Depends, HTTPException, Request, Query, Form
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse

from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List

from .db import Base, engine, get_db
from .models import Patient, Exam  # <- AQUI
from .schemas import PatientCreate, PatientOut, ExamOut
from .settings import settings
from .whatsapp import (
    send_template_message, send_text, send_document,
    get_media_url, download_media
)
from .storage import upload_bytes
from .processing import process_audio_bytes
from .report import build_pdf_bytes

import os

app = FastAPI(title="UroFlux MVP")

@app.on_event("startup")
def on_startup():
    # cria tabelas (MVP)
    Base.metadata.create_all(bind=engine)
    # sanity-check de conexão
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        print(f"[startup] WARNING: DB check falhou: {e}")

# static e templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# =======================
#   PACIENTES
# =======================
from .schemas import PatientCreate, PatientOut, ExamOut  # schemas aqui embaixo p/ clareza

@app.post("/patients", response_model=PatientOut)
def create_patient(p: PatientCreate, db: Session = Depends(get_db)):
    existing = (
        db.query(Patient)
          .filter((Patient.cpf == p.cpf) | (Patient.whatsapp == p.whatsapp))
          .first()
    )
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
        qry = qry.filter(
            (Patient.name.ilike(like)) |
            (Patient.cpf.ilike(like)) |
            (Patient.whatsapp.ilike(like))
        )
    return qry.order_by(Patient.id.desc()).limit(100).all()

@app.get("/patients/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    obj = db.get(Patient, patient_id)  # SQLAlchemy 2.x
    if not obj:
        raise HTTPException(404, "Paciente não encontrado.")
    return obj

# =======================
#   EXAMES
# =======================
@app.get("/exams", response_model=List[ExamOut])
def list_exams(patient_id: Optional[int] = None, db: Session = Depends(get_db)):
    qry = db.query(Exam)
    if patient_id:
        qry = qry.filter(Exam.patient_id == patient_id)
    return qry.order_by(Exam.id.desc()).limit(200).all()

@app.get("/exams/{exam_id}", response_model=ExamOut)
def get_exam(exam_id: int, db: Session = Depends(get_db)):
    obj = db.get(Exam, exam_id)
    if not obj:
        raise HTTPException(404, "Exame não encontrado.")
    return obj

# =======================
#   WhatsApp
# =======================
@app.post("/send-instructions/{patient_id}")
def send_instructions(patient_id: int, db: Session = Depends(get_db)):
    p = db.get(Patient, patient_id)
    if not p:
        raise HTTPException(404, "Paciente não encontrado.")
    try:
        send_template_message(
            to_whatsapp=p.whatsapp,
            template_name="uroflux_instrucoes_audio",  # ajuste ao seu template
            lang="pt_BR"
        )
    except Exception as e:
        raise HTTPException(500, f"Falha ao enviar WhatsApp: {e}")
    return {"ok": True}

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
                    from_wa = msg.get("from")  # número do paciente
                    _type = msg.get("type")

                    if _type == "audio":
                        media_id = msg.get("audio", {}).get("id")
                        msg_id = msg.get("id")
                        handle_audio_message(db, from_wa, media_id, msg_id)
                    else:
                        send_text(from_wa, "Por favor, envie uma mensagem de *áudio* para realizar o exame.")
        return {"ok": True}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

def handle_audio_message(db: Session, from_whatsapp: str, media_id: str, meta_message_id: str | None):
    # 1) localizar paciente
    patient = db.query(Patient).filter(Patient.whatsapp == from_whatsapp).first()
    if not patient:
        send_text(from_whatsapp, "Não encontrei seu cadastro. Peça ao seu médico para cadastrá-lo.")
        return

    # 2) criar exame como "processing"
    # ATENÇÃO: seu modelo Exam não tem 'meta_message_id' no momento.
    # Se desejar persistir, adicione a coluna no modelo + migre o banco.
    exam = Exam(patient_id=patient.id, status="processing")
    db.add(exam); db.commit(); db.refresh(exam)

    # 3) baixar áudio da Meta
    media_url = get_media_url(media_id)
    audio_bytes = download_media(media_url)

    # 4) subir áudio bruto (opcional, mas útil p/ auditoria)
    audio_key = f"audios/patient_{patient.id}_exam_{exam.id}.ogg"
    audio_url = upload_bytes(audio_key, audio_bytes, content_type="audio/ogg")
    exam.audio_url = audio_url
    db.commit()

    # 5) processar
    try:
        metrics = process_audio_bytes(audio_bytes)  # sua função retorna métricas
        pdf_bytes = build_pdf_bytes(patient.name, patient.cpf, metrics)

        pdf_key = f"reports/patient_{patient.id}_exam_{exam.id}.pdf"
        pdf_url = upload_bytes(pdf_key, pdf_bytes, content_type="application/pdf")
        # Se você tiver a coluna em ExamResult, salve lá. No MVP, guarde no próprio Exam:
        # exam.result = ExamResult(summary=..., pdf_url=pdf_url)  # se tiver a tabela
        exam.status = "done"
        # se quiser, crie fields pdf_url/summary em Exam (ou mantenha no ExamResult)
        # por enquanto, vamos só enviar o PDF ao paciente:
        db.commit()

        send_document(to_whatsapp=from_whatsapp, doc_url=pdf_url, caption="Seu resultado UroFlux")
    except Exception:
        exam.status = "failed"
        db.commit()
        send_text(from_whatsapp, "Houve um problema ao processar seu exame. Tente novamente mais tarde.")
        raise

# =======================
#   UI (médico)
# =======================
@app.get("/")
def home():
    return RedirectResponse(url="/web/patients")

@app.get("/web/patients")
def web_patients(request: Request, q: str | None = None, db: Session = Depends(get_db)):
    qry = db.query(Patient)
    if q:
        like = f"%{q}%"
        qry = qry.filter(
            (Patient.name.ilike(like)) |
            (Patient.cpf.ilike(like)) |
            (Patient.whatsapp.ilike(like))
        )
    patients = qry.order_by(Patient.id.desc()).limit(200).all()
    return templates.TemplateResponse(
        "patients_list.html",
        {"request": request, "patients": patients, "q": q or ""}
    )

@app.get("/web/patients/new")
def web_new_patient(request: Request):
    return templates.TemplateResponse(
        "patient_detail.html",
        {"request": request, "patient": None, "exams": [], "creating": True}
    )

@app.post("/web/patients/new")
def web_create_patient(
    request: Request,
    name: str = Form(...),
    cpf: str = Form(...),
    whatsapp: str = Form(...),
    db: Session = Depends(get_db)
):
    existing = (
        db.query(Patient)
          .filter((Patient.cpf == cpf) | (Patient.whatsapp == whatsapp))
          .first()
    )
    if existing:
        return RedirectResponse(url=f"/web/patients?error=duplicado", status_code=303)

    p = Patient(name=name, cpf=cpf, whatsapp=whatsapp)
    db.add(p); db.commit(); db.refresh(p)
    return RedirectResponse(url=f"/web/patients/{p.id}", status_code=303)

@app.get("/web/patients/{patient_id}")
def web_patient_detail(request: Request, patient_id: int, db: Session = Depends(get_db)):
    p = db.get(Patient, patient_id)
    if not p:
        return RedirectResponse(url="/web/patients", status_code=303)
    exams = db.query(Exam).filter(Exam.patient_id == patient_id).order_by(Exam.id.desc()).all()
    return templates.TemplateResponse(
        "patient_detail.html",
        {"request": request, "patient": p, "exams": exams, "creating": False}
    )

@app.post("/web/patients/{patient_id}/send-instructions")
def web_send_instructions(patient_id: int, db: Session = Depends(get_db)):
    p = db.get(Patient, patient_id)
    if not p:
        return RedirectResponse(url="/web/patients", status_code=303)
    try:
        send_template_message(
            to_whatsapp=p.whatsapp,
            template_name="uroflux_instrucoes_audio",
            lang="pt_BR"
        )
    except Exception:
        pass
    return RedirectResponse(url=f"/web/patients/{patient_id}", status_code=303)

@app.get("/web/exams")
def web_exams(request: Request, db: Session = Depends(get_db)):
    exams = db.query(Exam).order_by(Exam.id.desc()).limit(200).all()
    return templates.TemplateResponse("exams_list.html", {"request": request, "exams": exams})
