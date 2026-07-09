"""
=========================================================
HomeCare Enterprise
Servicio de Notificaciones (WhatsApp + Correo)

Envia automaticamente los documentos generados por el
sistema (ordenes medicas, examenes) al paciente por
WhatsApp y/o correo electronico.

Modo simulado: si no hay credenciales configuradas
(SMTP_HOST / WHATSAPP_TOKEN en el archivo .env), las
funciones no intentan conectarse a ningun servicio externo:
registran la notificacion en el log y devuelven
{"enviado": False, "modo": "simulado", ...} para que el
resto del flujo (crear la orden, guardarla en la BD) nunca
se vea interrumpido por falta de credenciales.
=========================================================
"""

import logging
import mimetypes
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from core.config import (
    PAIS_INDICATIVO_DEFECTO,
    SMTP_FROM,
    SMTP_FROM_NOMBRE,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USER,
    SMTP_USE_TLS,
    WHATSAPP_API_URL,
    WHATSAPP_PHONE_ID,
    WHATSAPP_TOKEN,
)

logger = logging.getLogger("homecare.notificaciones")


# ==========================================================
# UTILIDADES
# ==========================================================

def normalizar_celular(numero: str) -> str:
    """
    Deja el numero solo con digitos y le antepone el
    indicativo de pais si hace falta (por defecto, Colombia).
    """

    if not numero:
        return ""

    digitos = "".join(c for c in numero if c.isdigit())

    if not digitos:
        return ""

    if not digitos.startswith(PAIS_INDICATIVO_DEFECTO) and len(digitos) <= 10:
        digitos = f"{PAIS_INDICATIVO_DEFECTO}{digitos}"

    return digitos


# ==========================================================
# CORREO (SMTP)
# ==========================================================

def enviar_email(
    destinatario: str,
    asunto: str,
    cuerpo_html: str,
    adjunto_path: str | None = None,
) -> dict:

    if not destinatario:
        return {"enviado": False, "motivo": "El paciente no tiene correo registrado."}

    if not SMTP_HOST:
        logger.info(
            "[SIMULADO] Correo a %s | Asunto: %s | Adjunto: %s",
            destinatario, asunto, adjunto_path,
        )
        return {
            "enviado": False,
            "modo": "simulado",
            "motivo": "SMTP no configurado (ver .env: SMTP_HOST, SMTP_USER, SMTP_PASSWORD).",
        }

    try:
        mensaje = MIMEMultipart()
        mensaje["From"] = f"{SMTP_FROM_NOMBRE} <{SMTP_FROM}>"
        mensaje["To"] = destinatario
        mensaje["Subject"] = asunto

        mensaje.attach(MIMEText(cuerpo_html, "html", "utf-8"))

        if adjunto_path:
            ruta = Path(adjunto_path)
            if ruta.exists():
                tipo, _ = mimetypes.guess_type(str(ruta))
                with open(ruta, "rb") as archivo:
                    adjunto = MIMEApplication(
                        archivo.read(),
                        _subtype=(tipo.split("/")[-1] if tipo else "octet-stream"),
                    )
                    adjunto.add_header(
                        "Content-Disposition", "attachment", filename=ruta.name,
                    )
                    mensaje.attach(adjunto)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as servidor:
            if SMTP_USE_TLS:
                servidor.starttls()
            if SMTP_USER:
                servidor.login(SMTP_USER, SMTP_PASSWORD)
            servidor.sendmail(SMTP_FROM, [destinatario], mensaje.as_string())

        return {"enviado": True, "modo": "real"}

    except Exception as error:
        logger.exception("Error enviando correo a %s", destinatario)
        return {"enviado": False, "motivo": str(error)}


# ==========================================================
# WHATSAPP (Meta WhatsApp Business Cloud API)
# ==========================================================

def enviar_whatsapp(
    numero: str,
    mensaje: str,
    adjunto_url: str | None = None,
) -> dict:

    numero = normalizar_celular(numero)

    if not numero:
        return {"enviado": False, "motivo": "El paciente no tiene celular registrado."}

    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_ID:
        logger.info(
            "[SIMULADO] WhatsApp a %s | Mensaje: %s | Adjunto: %s",
            numero, mensaje, adjunto_url,
        )
        return {
            "enviado": False,
            "modo": "simulado",
            "motivo": (
                "WhatsApp Business API no configurada "
                "(ver .env: WHATSAPP_TOKEN, WHATSAPP_PHONE_ID)."
            ),
        }

    try:
        import requests

        url = f"{WHATSAPP_API_URL}/{WHATSAPP_PHONE_ID}/messages"
        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json",
        }

        if adjunto_url:
            payload = {
                "messaging_product": "whatsapp",
                "to": numero,
                "type": "document",
                "document": {
                    "link": adjunto_url,
                    "caption": mensaje,
                    "filename": "orden_medica.pdf",
                },
            }
        else:
            payload = {
                "messaging_product": "whatsapp",
                "to": numero,
                "type": "text",
                "text": {"body": mensaje},
            }

        respuesta = requests.post(url, headers=headers, json=payload, timeout=15)

        if respuesta.status_code >= 400:
            return {
                "enviado": False,
                "motivo": f"WhatsApp API respondió {respuesta.status_code}: {respuesta.text[:300]}",
            }

        return {"enviado": True, "modo": "real", "respuesta": respuesta.json()}

    except Exception as error:
        logger.exception("Error enviando WhatsApp a %s", numero)
        return {"enviado": False, "motivo": str(error)}
