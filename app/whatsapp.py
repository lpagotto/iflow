import requests
from .settings import settings

GRAPH = "https://graph.facebook.com/v19.0"

def send_template_message(to_whatsapp: str, template_name: str, lang="pt_BR", components=None):
    url = f"{GRAPH}/{settings.WHATSAPP_PHONE_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to_whatsapp,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": lang},
        }
    }
    if components:
        payload["template"]["components"] = components

    r = requests.post(url, json=payload, headers={"Authorization": f"Bearer {settings.META_TOKEN}"})
    r.raise_for_status()
    return r.json()

def send_text(to_whatsapp: str, text: str):
    url = f"{GRAPH}/{settings.WHATSAPP_PHONE_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to_whatsapp,
        "type": "text",
        "text": {"body": text}
    }
    r = requests.post(url, json=payload, headers={"Authorization": f"Bearer {settings.META_TOKEN}"})
    r.raise_for_status()
    return r.json()

def send_document(to_whatsapp: str, doc_url: str, caption: str = "Resultado do exame"):
    url = f"{GRAPH}/{settings.WHATSAPP_PHONE_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to_whatsapp,
        "type": "document",
        "document": {
            "link": doc_url,
            "filename": "resultado_uroflux.pdf",
            "caption": caption
        }
    }
    r = requests.post(url, json=payload, headers={"Authorization": f"Bearer {settings.META_TOKEN}"})
    r.raise_for_status()
    return r.json()

def get_media_url(media_id: str) -> str:
    url = f"{GRAPH}/{media_id}"
    r = requests.get(url, headers={"Authorization": f"Bearer {settings.META_TOKEN}"})
    r.raise_for_status()
    return r.json()["url"]

def download_media(media_url: str) -> bytes:
    r = requests.get(media_url, headers={"Authorization": f"Bearer {settings.META_TOKEN}"})
    r.raise_for_status()
    return r.content
