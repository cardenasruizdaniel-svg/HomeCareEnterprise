"""HomeCare Enterprise - Router: Configuración del Chatbot de WhatsApp"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from core.config import RECURSOS_DIR
from core.dependencies import requiere_permiso
from core.templates import templates
from database.database import consultar_todos

from services import configuracion_whatsapp_service as wa_config_service

router = APIRouter(prefix="/configuracion-whatsapp", tags=["Configuración WhatsApp"])


@router.get("/manual-pdf")
async def descargar_manual_whatsapp(usuario=Depends(requiere_permiso("chatbot_whatsapp"))):
    ruta = RECURSOS_DIR / "docs" / "manuales" / "MANUAL_CONEXION_WHATSAPP_ILUSTRADO.pdf"
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
    mensaje_despedida: str = Form(""),
    url_encuesta_satisfaccion: str = Form(""),
    usuario=Depends(requiere_permiso("chatbot_whatsapp")),
):
    wa_config_service.guardar(
        {
            "habilitado": 1 if habilitado else 0,
            "token_acceso": token_acceso,
            "id_numero_telefono": id_numero_telefono,
            "token_verificacion_webhook": token_verificacion_webhook,
            "mensaje_bienvenida": mensaje_bienvenida,
            "mensaje_despedida": mensaje_despedida,
            "url_encuesta_satisfaccion": url_encuesta_satisfaccion,
        },
        usuario.get("id") if isinstance(usuario, dict) else None,
    )
    return RedirectResponse(url="/configuracion-whatsapp?guardado=1", status_code=303)


# ==========================================================
# FLUJO DE CONVERSACIÓN (árbol de opciones del chatbot)
# ==========================================================

@router.get("/flujo/diagrama", response_class=HTMLResponse)
async def ver_diagrama_flujo(request: Request, usuario=Depends(requiere_permiso("chatbot_whatsapp"))):
    from services import whatsapp_flujo_service as flujo_service
    resultado = flujo_service.diagrama_mermaid()
    return templates.TemplateResponse(
        request=request, name="configuracion_whatsapp/diagrama.html",
        context={
            "usuario": usuario,
            "definicion_mermaid": resultado["definicion"],
            "detalles": resultado["detalles"],
        },
    )


@router.get("/flujo", response_class=HTMLResponse)
async def ver_flujo(request: Request, usuario=Depends(requiere_permiso("chatbot_whatsapp"))):
    from services import whatsapp_flujo_service as flujo_service
    return templates.TemplateResponse(
        request=request, name="configuracion_whatsapp/flujo.html",
        context={
            "usuario": usuario,
            "arbol": flujo_service.arbol_completo(),
            "opciones_padre": flujo_service.opciones_planas_para_padre(),
            "tipos_accion": flujo_service.TIPOS_ACCION,
            "marcadores": flujo_service.MARCADORES_DISPONIBLES,
            "error": request.query_params.get("error"),
            "guardado": request.query_params.get("guardado"),
        },
    )


@router.post("/flujo/construir-personalizado")
async def construir_personalizado(request: Request, usuario=Depends(requiere_permiso("chatbot_whatsapp"))):
    from services import whatsapp_flujo_service as flujo_service
    flujo_service.construir_flujo_personalizado_homecare(usuario.get("id") if isinstance(usuario, dict) else None)
    return RedirectResponse(url="/configuracion-whatsapp/flujo?guardado=1", status_code=303)


@router.post("/flujo/restaurar-plantilla")
async def restaurar_plantilla(request: Request, usuario=Depends(requiere_permiso("chatbot_whatsapp"))):
    from services import whatsapp_flujo_service as flujo_service
    flujo_service.restaurar_plantilla_homecare(usuario.get("id") if isinstance(usuario, dict) else None)
    return RedirectResponse(url="/configuracion-whatsapp/flujo?guardado=1", status_code=303)


@router.post("/flujo/crear")
async def crear_opcion_flujo(
    request: Request,
    padre_id: str = Form(""),
    texto_boton: str = Form(...),
    tipo_accion: str = Form(...),
    contenido_respuesta: str = Form(""),
    departamento: str = Form(""),
    orden: str = Form("0"),
    campos_solicitados: str = Form(""),
    usuario=Depends(requiere_permiso("chatbot_whatsapp")),
):
    from services import whatsapp_flujo_service as flujo_service
    try:
        flujo_service.crear_opcion(
            int(padre_id) if padre_id else None, texto_boton, tipo_accion,
            contenido_respuesta, departamento, int(orden or 0), campos_solicitados,
        )
    except ValueError as error:
        return RedirectResponse(url=f"/configuracion-whatsapp/flujo?error={error}", status_code=303)
    return RedirectResponse(url="/configuracion-whatsapp/flujo?guardado=1", status_code=303)


@router.post("/flujo/{opcion_id}/actualizar")
async def actualizar_opcion_flujo(
    request: Request,
    opcion_id: int,
    texto_boton: str = Form(...),
    tipo_accion: str = Form(...),
    contenido_respuesta: str = Form(""),
    departamento: str = Form(""),
    orden: str = Form("0"),
    campos_solicitados: str = Form(""),
    usuario=Depends(requiere_permiso("chatbot_whatsapp")),
):
    from services import whatsapp_flujo_service as flujo_service
    try:
        flujo_service.actualizar_opcion(opcion_id, texto_boton, tipo_accion, contenido_respuesta, departamento, int(orden or 0), campos_solicitados)
    except ValueError as error:
        return RedirectResponse(url=f"/configuracion-whatsapp/flujo?error={error}", status_code=303)
    return RedirectResponse(url="/configuracion-whatsapp/flujo?guardado=1", status_code=303)


@router.post("/flujo/{opcion_id}/eliminar")
async def eliminar_opcion_flujo(opcion_id: int, usuario=Depends(requiere_permiso("chatbot_whatsapp"))):
    from services import whatsapp_flujo_service as flujo_service
    flujo_service.eliminar_opcion(opcion_id)
    return RedirectResponse(url="/configuracion-whatsapp/flujo?guardado=1", status_code=303)


@router.post("/flujo/{opcion_id}/desactivar")
async def desactivar_opcion_flujo(opcion_id: int, usuario=Depends(requiere_permiso("chatbot_whatsapp"))):
    from services import whatsapp_flujo_service as flujo_service
    flujo_service.desactivar_opcion(opcion_id)
    return RedirectResponse(url="/configuracion-whatsapp/flujo?guardado=1", status_code=303)


@router.post("/flujo/{opcion_id}/activar")
async def activar_opcion_flujo(opcion_id: int, usuario=Depends(requiere_permiso("chatbot_whatsapp"))):
    from services import whatsapp_flujo_service as flujo_service
    flujo_service.activar_opcion(opcion_id)
    return RedirectResponse(url="/configuracion-whatsapp/flujo?guardado=1", status_code=303)
