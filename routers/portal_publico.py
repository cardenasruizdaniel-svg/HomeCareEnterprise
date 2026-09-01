"""
HomeCare Enterprise - Portal Público (Fase 2: PQR/SIAU)

Rutas SIN autenticación -- para que cualquier persona pueda
presentar una PQR o consultar su estado sin tener usuario del
sistema. Vive en el MISMO servidor (mismo dominio) que el
sistema interno, así que no hace falta configurar CORS ni una
API separada -- es simplemente un conjunto de rutas que no
pasan por 'requiere_permiso'.

Importante: estas rutas NUNCA deben devolver información
clínica ni datos sensibles del paciente -- solo lo necesario
para radicar y hacer seguimiento administrativo de la solicitud.
"""

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.templates import templates

from services import pqr_service as pqr
from services import configuracion_web_service as cw

router = APIRouter(prefix="/portal", tags=["Portal Público"])


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def inicio_portal(request: Request):
    return templates.TemplateResponse(
        request=request, name="portal/inicio.html",
        context={"config": cw.obtener_configuracion(), "servicios": cw.listar_servicios(solo_activos=True)},
    )


@router.get("/servicios", response_class=HTMLResponse)
async def servicios_portal(request: Request):
    return templates.TemplateResponse(
        request=request, name="portal/servicios.html",
        context={"servicios": cw.listar_servicios(solo_activos=True)},
    )


@router.get("/nosotros", response_class=HTMLResponse)
async def nosotros_portal(request: Request):
    return templates.TemplateResponse(
        request=request, name="portal/nosotros.html",
        context={"config": cw.obtener_configuracion()},
    )


@router.get("/contacto", response_class=HTMLResponse)
async def contacto_portal(request: Request):
    return templates.TemplateResponse(
        request=request, name="portal/contacto.html",
        context={
            "config": cw.obtener_configuracion(),
            "enviado": request.query_params.get("enviado"), "error": request.query_params.get("error"),
        },
    )


@router.post("/contacto/enviar")
async def enviar_contacto(
    nombre: str = Form(...), telefono: str = Form(""), correo: str = Form(""),
    mensaje: str = Form(...), motivo: str = Form("Solicitar información"),
):
    """
    El formulario de contacto reutiliza el mismo sistema PQR
    (tipo 'Solicitud') en vez de tener una tabla de mensajes
    aparte -- así toda comunicación entrante del portal
    público queda con el mismo radicado, línea de tiempo, y
    bandeja de gestión que ya existe, sin duplicar el concepto.
    """
    try:
        pqr.radicar_pqr(
            {
                "tipo": "Solicitud", "descripcion": mensaje, "asunto": motivo,
                "solicitante_nombre": nombre, "solicitante_relacion": "Otro",
                "solicitante_telefono": telefono, "solicitante_correo": correo,
                "canal": "Portal web",
            },
            es_publica=True,
        )
    except ValueError as error:
        return RedirectResponse(url=f"/portal/contacto?error={error}", status_code=303)
    return RedirectResponse(url="/portal/contacto?enviado=1", status_code=303)


@router.get("/atencion-usuario", response_class=HTMLResponse)
async def atencion_usuario_portal(request: Request):
    return templates.TemplateResponse(request=request, name="portal/atencion_usuario.html", context={})


@router.get("/pqr", response_class=HTMLResponse)
async def formulario_pqr(request: Request):
    return templates.TemplateResponse(
        request=request, name="portal/pqr_formulario.html",
        context={"tipos": pqr.TIPOS_PQR, "relaciones": pqr.RELACIONES_SOLICITANTE, "error": request.query_params.get("error")},
    )


@router.post("/pqr/enviar")
async def enviar_pqr(
    tipo: str = Form(...), descripcion: str = Form(...), solicitante_nombre: str = Form(...),
    solicitante_relacion: str = Form("Paciente"), solicitante_documento: str = Form(""),
    solicitante_telefono: str = Form(""), solicitante_correo: str = Form(""), asunto: str = Form(""),
):
    try:
        resultado = pqr.radicar_pqr(
            {
                "tipo": tipo, "descripcion": descripcion, "asunto": asunto,
                "solicitante_nombre": solicitante_nombre, "solicitante_relacion": solicitante_relacion,
                "solicitante_documento": solicitante_documento, "solicitante_telefono": solicitante_telefono,
                "solicitante_correo": solicitante_correo, "canal": "Portal web",
            },
            es_publica=True,
        )
    except ValueError as error:
        return RedirectResponse(url=f"/portal/pqr?error={error}", status_code=303)

    return RedirectResponse(
        url=f"/portal/pqr/confirmacion?radicado={resultado['radicado']}&clave={resultado['clave_seguimiento']}",
        status_code=303,
    )


@router.get("/pqr/confirmacion", response_class=HTMLResponse)
async def confirmacion_pqr(request: Request):
    radicado = request.query_params.get("radicado")
    clave = request.query_params.get("clave")
    if not radicado or not clave:
        raise HTTPException(status_code=404, detail="No se encontró la confirmación solicitada.")
    return templates.TemplateResponse(
        request=request, name="portal/pqr_confirmacion.html",
        context={"radicado": radicado, "clave": clave},
    )


@router.get("/pqr/seguimiento", response_class=HTMLResponse)
async def formulario_seguimiento(request: Request):
    return templates.TemplateResponse(
        request=request, name="portal/pqr_seguimiento.html",
        context={"resultado": None, "error": request.query_params.get("error")},
    )


@router.post("/pqr/seguimiento", response_class=HTMLResponse)
async def consultar_seguimiento(request: Request, radicado: str = Form(...), clave: str = Form(...)):
    resultado = pqr.consultar_estado_publico(radicado, clave)
    if not resultado:
        return templates.TemplateResponse(
            request=request, name="portal/pqr_seguimiento.html",
            context={"resultado": None, "error": "No se encontró ninguna PQR con ese radicado y esa clave de seguimiento. Verifique que estén escritos exactamente como se los entregamos."},
        )
    return templates.TemplateResponse(
        request=request, name="portal/pqr_seguimiento.html",
        context={"resultado": resultado, "error": None},
    )


# ==========================================================
# TURNERO -- solicitar y consultar turno desde el portal público
# ==========================================================

from services import turnero_service as turnero


@router.get("/turno", response_class=HTMLResponse)
async def turno_formulario(request: Request):
    return templates.TemplateResponse(
        request=request, name="portal/turno_formulario.html",
        context={"servicios": turnero.listar_servicios(solo_activos=True), "error": request.query_params.get("error")},
    )


@router.post("/turno/solicitar")
async def turno_solicitar(
    servicio_id: int = Form(...), documento: str = Form(...),
    nombre_visitante: str = Form(""), fecha_nacimiento: str = Form(""),
):
    try:
        turno = turnero.crear_turno(
            {
                "servicio_id": servicio_id, "documento": documento,
                "nombre_visitante": nombre_visitante or None, "fecha_nacimiento": fecha_nacimiento or None,
            },
            canal="Web",
        )
    except ValueError as error:
        return RedirectResponse(url=f"/portal/turno?error={error}", status_code=303)
    return RedirectResponse(
        url=f"/portal/turno/confirmacion?numero={turno['numero_completo']}&documento={documento}",
        status_code=303,
    )


@router.get("/turno/confirmacion", response_class=HTMLResponse)
async def turno_confirmacion(request: Request):
    numero = request.query_params.get("numero")
    documento = request.query_params.get("documento")
    if not numero or not documento:
        raise HTTPException(status_code=404, detail="No se encontró la confirmación solicitada.")
    resultado = turnero.consultar_estado_publico(numero, documento)
    if not resultado:
        raise HTTPException(status_code=404, detail="No se encontró el turno solicitado.")
    return templates.TemplateResponse(
        request=request, name="portal/turno_confirmacion.html",
        context={"turno": resultado, "documento": documento},
    )


@router.get("/turno/consultar", response_class=HTMLResponse)
async def turno_consultar_formulario(request: Request):
    return templates.TemplateResponse(
        request=request, name="portal/turno_consultar.html",
        context={"resultado": None, "error": request.query_params.get("error")},
    )


@router.post("/turno/consultar", response_class=HTMLResponse)
async def turno_consultar_resultado(request: Request, numero: str = Form(...), documento: str = Form(...)):
    resultado = turnero.consultar_estado_publico(numero, documento)
    if not resultado:
        return templates.TemplateResponse(
            request=request, name="portal/turno_consultar.html",
            context={"resultado": None, "error": "No se encontró ningún turno con ese número y ese documento. Verifique que estén escritos correctamente."},
        )
    return templates.TemplateResponse(
        request=request, name="portal/turno_consultar.html",
        context={"resultado": resultado, "error": None},
    )
