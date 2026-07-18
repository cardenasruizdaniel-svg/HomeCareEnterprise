"""
HomeCare Enterprise - Router: Firma Remota por Código QR

Las rutas /firma-remota/{token} y su envio son PUBLICAS a
proposito (sin exigir sesion iniciada): la persona que firma
desde su propio celular -- paciente, acudiente o profesional
-- normalmente no tiene ni deberia necesitar una cuenta en el
sistema para poder firmar. La seguridad de esta pagina depende
de que el token sea unico, de un solo uso, y de que solo se
entregue a traves del QR generado por un usuario ya
autenticado en el sistema principal.
"""

from fastapi import APIRouter, Body, Depends, Request
from fastapi.responses import HTMLResponse

from core.dependencies import requiere_permiso
from core.templates import templates

from services import solicitudes_firma_service

router = APIRouter(prefix="/firma-remota", tags=["Firma Remota"])


# ==========================================
# CREACIÓN DE LA SOLICITUD (requiere sesión:
# la usa el usuario del sistema para generar
# el QR desde la pantalla de escritorio)
# ==========================================

@router.post("/crear")
async def crear(request: Request, datos: dict = Body(...), usuario=Depends(requiere_permiso("pacientes"))):
    try:
        token = solicitudes_firma_service.crear_solicitud(datos["tipo"], int(datos["referencia_id"]))
        url_completa = str(request.base_url).rstrip("/") + f"/firma-remota/{token}"
        return {"ok": True, "token": token, "url": url_completa}
    except ValueError as error:
        return {"ok": False, "error": str(error)}


@router.get("/estado/{token}")
async def estado(token: str, _actor=Depends(requiere_permiso("pacientes"))):
    solicitud = solicitudes_firma_service.obtener_por_token(token)
    if not solicitud:
        return {"estado": "No encontrada"}
    return {"estado": solicitud["estado"], "firma_base64": solicitud.get("firma_base64")}


# ==========================================
# PÁGINA DE FIRMA (pública, sin sesión)
# ==========================================

@router.get("/{token}", response_class=HTMLResponse)
async def pagina_firma(request: Request, token: str):
    solicitud = solicitudes_firma_service.obtener_por_token(token)

    return templates.TemplateResponse(
        request=request, name="firma_remota/firmar.html",
        context={"token": token, "solicitud": solicitud},
    )


@router.post("/{token}/enviar")
async def enviar_firma(token: str, datos: dict = Body(...)):
    try:
        resultado = solicitudes_firma_service.completar_firma(
            token,
            firma_base64=datos.get("firma_base64"),
            firmante=datos.get("firmante", ""),
            nombre_firmante=datos.get("nombre_firmante", ""),
            documento_firmante=datos.get("documento_firmante", ""),
            parentesco_firmante=datos.get("parentesco_firmante", ""),
        )
        return resultado
    except ValueError as error:
        return {"ok": False, "error": str(error)}
