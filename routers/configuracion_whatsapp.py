"""HomeCare Enterprise - Router: Configuración del Chatbot de WhatsApp"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from core.config import BASE_DIR
from core.dependencies import requiere_permiso
from core.templates import templates
from database.database import consultar_todos

from services import configuracion_whatsapp_service as wa_config_service

router = APIRouter(prefix="/configuracion-whatsapp", tags=["Configuración WhatsApp"])


@router.get("/manual-pdf")
async def descargar_manual_whatsapp(usuario=Depends(requiere_permiso("chatbot_whatsapp"))):
    ruta = BASE_DIR / "docs" / "manuales" / "MANUAL_CONEXION_WHATSAPP.pdf"
    return FileResponse(ruta, media_type="application/pdf", filename="Manual_Conexion_WhatsApp_HomeCare.pdf")


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def ver(request: Request, usuario=Depends(requiere_permiso("chatbot_whatsapp"))):
    config = wa_config_service.obtener()
    for campo in wa_config_service.CAMPOS_SENSIBLES:
        config[f"_{campo}_configurado"] = bool(config.get(campo))
        config[campo] = ""

    conversaciones_recientes = consultar_todos(
        """
        SELECT wc.*, p.primer_nombre, p.primer_apellido
        FROM whatsapp_conversaciones wc
        LEFT JOIN pacientes p ON p.id = wc.paciente_id
        ORDER BY wc.fecha DESC LIMIT 30
        """
    )

    return templates.TemplateResponse(
        request=request, name="configuracion_whatsapp/formulario.html",
        context={
            "usuario": usuario, "config": config,
            "conversaciones": [dict(c) for c in conversaciones_recientes],
            "guardado": request.query_params.get("guardado"),
        },
    )


@router.post("/guardar")
async def guardar(
    request: Request,
    habilitado: str = Form(""),
    token_acceso: str = Form(""),
    id_numero_telefono: str = Form(""),
    token_verificacion_webhook: str = Form(""),
    mensaje_bienvenida: str = Form(""),
    usuario=Depends(requiere_permiso("chatbot_whatsapp")),
):
    wa_config_service.guardar(
        {
            "habilitado": 1 if habilitado else 0,
            "token_acceso": token_acceso,
            "id_numero_telefono": id_numero_telefono,
            "token_verificacion_webhook": token_verificacion_webhook,
            "mensaje_bienvenida": mensaje_bienvenida,
        },
        usuario.get("id") if isinstance(usuario, dict) else None,
    )
    return RedirectResponse(url="/configuracion-whatsapp?guardado=1", status_code=303)
