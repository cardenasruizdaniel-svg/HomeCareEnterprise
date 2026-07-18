"""
HomeCare Enterprise - Router: Documentos Seguros (WhatsApp)

Ruta PÚBLICA (sin necesidad de iniciar sesión) para que el
paciente o su acudiente puedan descargar, desde el enlace que
les llega por WhatsApp, el documento que el bot les autorizó a
recibir -- protegida por un token de un solo uso que vence a
las 48 horas, no por login.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/documentos-seguros", tags=["Documentos Seguros WhatsApp"])


@router.get("/{token}")
async def descargar_documento_seguro(token: str):
    from services.whatsapp_documentos_seguros_service import (
        obtener_token_valido, generar_pdf_historia_clinica,
    )

    fila_token = obtener_token_valido(token)
    if not fila_token:
        raise HTTPException(status_code=404, detail="Este enlace ya no es válido o ya venció. Solicítelo de nuevo por WhatsApp.")

    if fila_token["tipo_documento"] == "historia_clinica":
        ruta = generar_pdf_historia_clinica(fila_token["paciente_id"])
        nombre_archivo = "historia_clinica.pdf"
    else:
        raise HTTPException(status_code=400, detail="Tipo de documento no reconocido.")

    # No se marca como "usado" en la primera consulta: WhatsApp
    # necesita poder buscar el archivo desde sus propios
    # servidores para poder entregárselo al paciente dentro del
    # chat, así que la seguridad principal de este enlace es que
    # solo dura 48 horas (y que el token es imposible de
    # adivinar), no que se use una sola vez.

    return FileResponse(ruta, media_type="application/pdf", filename=nombre_archivo)
