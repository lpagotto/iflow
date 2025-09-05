from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO

def build_pdf_bytes(patient_name: str, cpf: str, metrics: dict) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, h-50, "UroFlux - Resultado do Exame")

    c.setFont("Helvetica", 12)
    c.drawString(50, h-90, f"Paciente: {patient_name}")
    c.drawString(50, h-110, f"CPF: {cpf}")

    y = h-150
    for k, v in metrics.items():
        c.drawString(50, y, f"{k.replace('_',' ').title()}: {v}")
        y -= 20

    c.showPage()
    c.save()
    return buffer.getvalue()
