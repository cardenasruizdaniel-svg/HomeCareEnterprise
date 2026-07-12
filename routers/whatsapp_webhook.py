"""
HomeCare Enterprise - Webhook del Chatbot de WhatsApp

Estas rutas NO requieren sesión iniciada a propósito -- son
las que Meta (WhatsApp Business Cloud API) llama directamente
desde sus servidores para verificar el webhook y para
entregarle los mensajes entrantes de los pacientes.

GET  /webhook/whatsapp -> verificación inicial (Meta la llama
     una sola vez, al registrar la URL del webhook en su panel).
POST /webhook/whatsapp -> mensajes entrantes reales.
"""

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from database.database import consultar_uno

router = APIRouter(prefix="/webhook/whatsapp", tags=["Chatbot WhatsApp"])


def _config_actual() -> dict:
    fila = consultar_uno("SELECT * FROM configuracion_whatsapp WHERE id=1")
    return dict(fila) if fila else {}


@router.get("")
@router.get("/")
async def verificar_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """
    Meta llama esto UNA VEZ al momento de configurar el
    webhook en su panel de desarrolladores, para confirmar que
    el servidor es de verdad el dueño de esta URL. Si el
    "token de verificación" coincide con el que se configuró
    en Configuración de WhatsApp, se responde con el
    "challenge" que Meta mandó, y queda verificado.
    """
    config = _config_actual()
    token_esperado = config.get("token_verificacion_webhook")

    if hub_mode == "subscribe" and token_esperado and hub_verify_token == token_esperado:
        return PlainTextResponse(hub_challenge or "")

    return JSONResponse(status_code=403, content={"error": "Token de verificación inválido."})


@router.post("")
@router.post("/")
async def recibir_mensaje(request: Request):
    """
    Aquí llegan los mensajes reales que los pacientes le
    escriben al número de WhatsApp de la IPS. Se procesa cada
    mensaje de texto entrante con el chatbot, y se responde
    automáticamente.
    """
    config = _config_actual()
    if not config.get("habilitado"):
        return {"ok": True, "motivo": "Chatbot deshabilitado"}

    datos = await request.json()

    try:
        entradas = datos.get("entry", [])
        for entrada in entradas:
            for cambio in entrada.get("changes", []):
                valor = cambio.get("value", {})
                mensajes = valor.get("messages", [])

                for mensaje in mensajes:
                    numero_remitente = mensaje.get("from")
                    tipo_mensaje = mensaje.get("type")

                    if tipo_mensaje == "text":
                        texto = mensaje.get("text", {}).get("body", "")
                    elif tipo_mensaje == "button":
                        texto = mensaje.get("button", {}).get("text", "")
                    elif tipo_mensaje == "interactive":
                        interactivo = mensaje.get("interactive", {})
                        texto = (
                            interactivo.get("button_reply", {}).get("title")
                            or interactivo.get("list_reply", {}).get("title")
                            or ""
                        )
                    else:
                        texto = ""

                    if numero_remitente and texto:
                        from services.whatsapp_chatbot_service import procesar_mensaje_entrante
                        procesar_mensaje_entrante(numero_remitente, texto)

    except Exception:
        # Nunca se le devuelve un error a Meta por un problema
        # interno del chatbot -- si no, Meta reintenta entregar
        # el mismo mensaje una y otra vez. Se registra el error
        # y se responde "ok" igual.
        import logging
        logging.getLogger(__name__).exception("Error procesando webhook de WhatsApp")

    return {"ok": True}
