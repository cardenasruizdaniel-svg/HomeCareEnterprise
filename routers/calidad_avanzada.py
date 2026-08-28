"""HomeCare Enterprise - Router: Sistema Integral de Gestión de Calidad (Fase 1)"""

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.dependencies import requiere_permiso
from core.templates import templates

from services import calidad_avanzada_service as ca

router = APIRouter(prefix="/gestion-calidad", tags=["Sistema Integral de Gestión de Calidad"])


def _id_usuario(usuario):
    return usuario.get("id") if isinstance(usuario, dict) else None


# ==========================================================
# DASHBOARD
# ==========================================================

@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, usuario=Depends(requiere_permiso("calidad"))):
    return templates.TemplateResponse(
        request=request, name="calidad_avanzada/dashboard.html",
        context={"usuario": usuario, "resumen": ca.resumen_dashboard_calidad()},
    )


# ==========================================================
# MOTOR DE NORMATIVIDAD
# ==========================================================

@router.get("/normas", response_class=HTMLResponse)
async def ver_normas(request: Request, usuario=Depends(requiere_permiso("calidad"))):
    from services import profesionales_service
    return templates.TemplateResponse(
        request=request, name="calidad_avanzada/normas.html",
        context={
            "usuario": usuario, "normas": ca.listar_normas(), "tipos": ca.TIPOS_NORMA, "estados": ca.ESTADOS_NORMA,
            "profesionales": profesionales_service.activos(),
            "guardado": request.query_params.get("guardado"), "error": request.query_params.get("error"),
        },
    )


@router.post("/normas/crear")
async def crear_norma(request: Request, usuario=Depends(requiere_permiso("calidad"))):
    datos = dict(await request.form())
    try:
        ca.crear_norma(datos, usuario_id=_id_usuario(usuario))
    except ValueError as error:
        return RedirectResponse(url=f"/gestion-calidad/normas?error={error}", status_code=303)
    return RedirectResponse(url="/gestion-calidad/normas?guardado=1", status_code=303)


@router.post("/normas/{norma_id}/estado")
async def cambiar_estado_norma(norma_id: int, estado: str = Form(...), usuario=Depends(requiere_permiso("calidad"))):
    try:
        ca.actualizar_estado_norma(norma_id, estado)
    except ValueError as error:
        return RedirectResponse(url=f"/gestion-calidad/normas?error={error}", status_code=303)
    return RedirectResponse(url="/gestion-calidad/normas?guardado=1", status_code=303)


# ==========================================================
# PAMEC
# ==========================================================

@router.get("/pamec", response_class=HTMLResponse)
async def ver_pamec(request: Request, usuario=Depends(requiere_permiso("calidad"))):
    from services import profesionales_service
    return templates.TemplateResponse(
        request=request, name="calidad_avanzada/pamec_lista.html",
        context={
            "usuario": usuario, "ciclos": ca.listar_ciclos_pamec(), "estados": ca.ESTADOS_PAMEC,
            "profesionales": profesionales_service.activos(), "normas": ca.listar_normas(),
            "guardado": request.query_params.get("guardado"), "error": request.query_params.get("error"),
        },
    )


@router.post("/pamec/crear")
async def crear_pamec(request: Request, usuario=Depends(requiere_permiso("calidad"))):
    datos = dict(await request.form())
    try:
        ca.crear_ciclo_pamec(datos, usuario_id=_id_usuario(usuario))
    except ValueError as error:
        return RedirectResponse(url=f"/gestion-calidad/pamec?error={error}", status_code=303)
    return RedirectResponse(url="/gestion-calidad/pamec?guardado=1", status_code=303)


@router.get("/pamec/{ciclo_id}", response_class=HTMLResponse)
async def ver_ciclo_pamec(request: Request, ciclo_id: int, usuario=Depends(requiere_permiso("calidad"))):
    from services import profesionales_service
    ciclo = ca.obtener_ciclo_pamec(ciclo_id)
    if not ciclo:
        raise HTTPException(status_code=404, detail="El ciclo PAMEC no existe.")
    return templates.TemplateResponse(
        request=request, name="calidad_avanzada/pamec_detalle.html",
        context={
            "usuario": usuario, "ciclo": ciclo, "estados_proceso": ca.ESTADOS_PROCESO_PAMEC,
            "profesionales": profesionales_service.activos(),
            "guardado": request.query_params.get("guardado"), "error": request.query_params.get("error"),
        },
    )


@router.post("/pamec/{ciclo_id}/estado")
async def cambiar_estado_pamec(ciclo_id: int, estado: str = Form(...), usuario=Depends(requiere_permiso("calidad"))):
    try:
        ca.actualizar_estado_pamec(ciclo_id, estado)
    except ValueError as error:
        return RedirectResponse(url=f"/gestion-calidad/pamec/{ciclo_id}?error={error}", status_code=303)
    return RedirectResponse(url=f"/gestion-calidad/pamec/{ciclo_id}?guardado=1", status_code=303)


@router.post("/pamec/{ciclo_id}/procesos/agregar")
async def agregar_proceso_pamec(request: Request, ciclo_id: int, usuario=Depends(requiere_permiso("calidad"))):
    datos = dict(await request.form())
    try:
        ca.agregar_proceso_pamec(ciclo_id, datos)
    except ValueError as error:
        return RedirectResponse(url=f"/gestion-calidad/pamec/{ciclo_id}?error={error}", status_code=303)
    return RedirectResponse(url=f"/gestion-calidad/pamec/{ciclo_id}?guardado=1", status_code=303)


@router.post("/pamec/procesos/{proceso_id}/resultado")
async def actualizar_resultado_proceso(
    proceso_id: int, ciclo_id: int = Form(...), resultado: str = Form(""), porcentaje_cumplimiento: str = Form(""),
    brecha: str = Form(""), analisis: str = Form(""), estado: str = Form(...),
    usuario=Depends(requiere_permiso("calidad")),
):
    try:
        ca.actualizar_resultado_proceso_pamec(
            proceso_id, resultado, float(porcentaje_cumplimiento) if porcentaje_cumplimiento else None, brecha, analisis, estado,
        )
    except ValueError as error:
        return RedirectResponse(url=f"/gestion-calidad/pamec/{ciclo_id}?error={error}", status_code=303)
    return RedirectResponse(url=f"/gestion-calidad/pamec/{ciclo_id}?guardado=1", status_code=303)


# ==========================================================
# AUDITORÍAS DE CALIDAD
# ==========================================================

@router.get("/auditorias", response_class=HTMLResponse)
async def ver_auditorias(request: Request, usuario=Depends(requiere_permiso("calidad"))):
    from services import profesionales_service
    return templates.TemplateResponse(
        request=request, name="calidad_avanzada/auditorias_lista.html",
        context={
            "usuario": usuario, "auditorias": ca.listar_auditorias(), "tipos": ca.TIPOS_AUDITORIA,
            "profesionales": profesionales_service.activos(), "normas": ca.listar_normas(),
            "ciclos_pamec": ca.listar_ciclos_pamec(),
            "guardado": request.query_params.get("guardado"), "error": request.query_params.get("error"),
        },
    )


@router.post("/auditorias/crear")
async def crear_auditoria(request: Request, usuario=Depends(requiere_permiso("calidad"))):
    datos = dict(await request.form())
    try:
        ca.crear_auditoria(datos, usuario_id=_id_usuario(usuario))
    except ValueError as error:
        return RedirectResponse(url=f"/gestion-calidad/auditorias?error={error}", status_code=303)
    return RedirectResponse(url="/gestion-calidad/auditorias?guardado=1", status_code=303)


@router.get("/auditorias/{auditoria_id}", response_class=HTMLResponse)
async def ver_auditoria(request: Request, auditoria_id: int, usuario=Depends(requiere_permiso("calidad"))):
    from services import profesionales_service
    auditoria = ca.obtener_auditoria(auditoria_id)
    if not auditoria:
        raise HTTPException(status_code=404, detail="La auditoría no existe.")
    return templates.TemplateResponse(
        request=request, name="calidad_avanzada/auditoria_detalle.html",
        context={
            "usuario": usuario, "auditoria": auditoria, "clasificaciones": ca.CLASIFICACIONES_HALLAZGO,
            "profesionales": profesionales_service.activos(), "normas": ca.listar_normas(),
            "guardado": request.query_params.get("guardado"), "error": request.query_params.get("error"),
        },
    )


@router.post("/auditorias/{auditoria_id}/cerrar")
async def cerrar_auditoria(auditoria_id: int, resultado_general: str = Form(...), observaciones: str = Form(""), usuario=Depends(requiere_permiso("calidad"))):
    ca.cerrar_auditoria(auditoria_id, resultado_general, observaciones)
    return RedirectResponse(url=f"/gestion-calidad/auditorias/{auditoria_id}?guardado=1", status_code=303)


@router.post("/auditorias/{auditoria_id}/hallazgos/crear")
async def crear_hallazgo_desde_auditoria(request: Request, auditoria_id: int, usuario=Depends(requiere_permiso("calidad"))):
    datos = dict(await request.form())
    datos["auditoria_id"] = auditoria_id
    datos["fuente"] = "Auditoría"
    try:
        ca.crear_hallazgo(datos, usuario_id=_id_usuario(usuario))
    except ValueError as error:
        return RedirectResponse(url=f"/gestion-calidad/auditorias/{auditoria_id}?error={error}", status_code=303)
    return RedirectResponse(url=f"/gestion-calidad/auditorias/{auditoria_id}?guardado=1", status_code=303)


# ==========================================================
# HALLAZGOS / NO CONFORMIDADES
# ==========================================================

@router.get("/hallazgos", response_class=HTMLResponse)
async def ver_hallazgos(request: Request, usuario=Depends(requiere_permiso("calidad"))):
    return templates.TemplateResponse(
        request=request, name="calidad_avanzada/hallazgos_lista.html",
        context={"usuario": usuario, "hallazgos": ca.listar_hallazgos(), "clasificaciones": ca.CLASIFICACIONES_HALLAZGO},
    )


@router.get("/hallazgos/{hallazgo_id}", response_class=HTMLResponse)
async def ver_hallazgo(request: Request, hallazgo_id: int, usuario=Depends(requiere_permiso("calidad"))):
    from services import profesionales_service
    hallazgo = ca.obtener_hallazgo(hallazgo_id)
    if not hallazgo:
        raise HTTPException(status_code=404, detail="El hallazgo no existe.")
    return templates.TemplateResponse(
        request=request, name="calidad_avanzada/hallazgo_detalle.html",
        context={
            "usuario": usuario, "hallazgo": hallazgo, "tipos_accion": ca.TIPOS_ACCION,
            "profesionales": profesionales_service.activos(),
            "guardado": request.query_params.get("guardado"), "error": request.query_params.get("error"),
        },
    )


@router.post("/hallazgos/{hallazgo_id}/causa-raiz")
async def registrar_causa_raiz(hallazgo_id: int, causa_raiz: str = Form(...), metodologia_analisis: str = Form(""), usuario=Depends(requiere_permiso("calidad"))):
    try:
        ca.registrar_analisis_causa(hallazgo_id, causa_raiz, metodologia_analisis)
    except ValueError as error:
        return RedirectResponse(url=f"/gestion-calidad/hallazgos/{hallazgo_id}?error={error}", status_code=303)
    return RedirectResponse(url=f"/gestion-calidad/hallazgos/{hallazgo_id}?guardado=1", status_code=303)


@router.post("/hallazgos/{hallazgo_id}/cerrar")
async def cerrar_hallazgo(hallazgo_id: int, usuario=Depends(requiere_permiso("calidad"))):
    try:
        ca.cerrar_hallazgo(hallazgo_id)
    except ValueError as error:
        return RedirectResponse(url=f"/gestion-calidad/hallazgos/{hallazgo_id}?error={error}", status_code=303)
    return RedirectResponse(url=f"/gestion-calidad/hallazgos/{hallazgo_id}?guardado=1", status_code=303)


# ==========================================================
# ACCIONES DE MEJORA (CAPA)
# ==========================================================

@router.post("/hallazgos/{hallazgo_id}/acciones/crear")
async def crear_accion(request: Request, hallazgo_id: int, usuario=Depends(requiere_permiso("calidad"))):
    datos = dict(await request.form())
    try:
        ca.crear_accion(hallazgo_id, datos, usuario_id=_id_usuario(usuario))
    except ValueError as error:
        return RedirectResponse(url=f"/gestion-calidad/hallazgos/{hallazgo_id}?error={error}", status_code=303)
    return RedirectResponse(url=f"/gestion-calidad/hallazgos/{hallazgo_id}?guardado=1", status_code=303)


@router.post("/acciones/{accion_id}/ejecutar")
async def ejecutar_accion(accion_id: int, hallazgo_id: int = Form(...), fecha_ejecucion: str = Form(...), evidencia: str = Form(""), usuario=Depends(requiere_permiso("calidad"))):
    try:
        ca.ejecutar_accion(accion_id, fecha_ejecucion, evidencia)
    except ValueError as error:
        return RedirectResponse(url=f"/gestion-calidad/hallazgos/{hallazgo_id}?error={error}", status_code=303)
    return RedirectResponse(url=f"/gestion-calidad/hallazgos/{hallazgo_id}?guardado=1", status_code=303)


@router.post("/acciones/{accion_id}/verificar")
async def verificar_accion(
    accion_id: int, hallazgo_id: int = Form(...), fue_eficaz: str = Form(...), verificacion_eficacia: str = Form(...),
    usuario=Depends(requiere_permiso("calidad")),
):
    # 'verificado_por_id' hace referencia a la tabla profesionales
    # (no a usuarios) -- se busca el profesional asociado a quien
    # inició sesión, y si no tiene uno vinculado (ej. un usuario
    # puramente administrativo), se deja sin asignar en vez de
    # violar la relación con un id que no corresponde.
    from database.database import consultar_uno
    profesional = consultar_uno("SELECT id FROM profesionales WHERE usuario_id=?", (_id_usuario(usuario),))
    profesional_id = dict(profesional)["id"] if profesional else None

    ca.verificar_eficacia_accion(accion_id, fue_eficaz == "si", verificacion_eficacia, verificado_por_id=profesional_id)
    return RedirectResponse(url=f"/gestion-calidad/hallazgos/{hallazgo_id}?guardado=1", status_code=303)


# ==========================================================
# MATRIZ DE RIESGOS
# ==========================================================

@router.get("/riesgos", response_class=HTMLResponse)
async def ver_riesgos(request: Request, usuario=Depends(requiere_permiso("calidad"))):
    from services import profesionales_service
    return templates.TemplateResponse(
        request=request, name="calidad_avanzada/riesgos_lista.html",
        context={
            "usuario": usuario, "riesgos": ca.listar_riesgos(), "probabilidades": ca.PROBABILIDADES,
            "impactos": ca.IMPACTOS, "estados": ca.ESTADOS_RIESGO,
            "profesionales": profesionales_service.activos(),
            "guardado": request.query_params.get("guardado"), "error": request.query_params.get("error"),
        },
    )


@router.post("/riesgos/crear")
async def crear_riesgo(request: Request, usuario=Depends(requiere_permiso("calidad"))):
    datos = dict(await request.form())
    try:
        ca.crear_riesgo(datos, usuario_id=_id_usuario(usuario))
    except ValueError as error:
        return RedirectResponse(url=f"/gestion-calidad/riesgos?error={error}", status_code=303)
    return RedirectResponse(url="/gestion-calidad/riesgos?guardado=1", status_code=303)


@router.post("/riesgos/{riesgo_id}/tratamiento")
async def actualizar_tratamiento_riesgo(
    riesgo_id: int, riesgo_residual: str = Form(""), tratamiento: str = Form(""),
    accion: str = Form(""), estado: str = Form(...), usuario=Depends(requiere_permiso("calidad")),
):
    try:
        ca.actualizar_tratamiento_riesgo(riesgo_id, riesgo_residual, tratamiento, accion, estado)
    except ValueError as error:
        return RedirectResponse(url=f"/gestion-calidad/riesgos?error={error}", status_code=303)
    return RedirectResponse(url="/gestion-calidad/riesgos?guardado=1", status_code=303)


# ==========================================================
# SEGURIDAD DEL PACIENTE
# ==========================================================

@router.get("/seguridad-paciente", response_class=HTMLResponse)
async def ver_eventos_seguridad(request: Request, usuario=Depends(requiere_permiso("calidad"))):
    from services import profesionales_service
    from services.pacientes_service import PacientesService
    return templates.TemplateResponse(
        request=request, name="calidad_avanzada/eventos_seguridad_lista.html",
        context={
            "usuario": usuario, "eventos": ca.listar_eventos_seguridad(), "tipos": ca.TIPOS_EVENTO_SEGURIDAD,
            "severidades": ca.SEVERIDADES_EVENTO, "profesionales": profesionales_service.activos(),
            "pacientes": PacientesService.listar(),
            "guardado": request.query_params.get("guardado"), "error": request.query_params.get("error"),
        },
    )


@router.post("/seguridad-paciente/crear")
async def crear_evento_seguridad(request: Request, usuario=Depends(requiere_permiso("calidad"))):
    datos = dict(await request.form())
    try:
        evento_id = ca.crear_evento_seguridad(datos, usuario_id=_id_usuario(usuario))
    except ValueError as error:
        return RedirectResponse(url=f"/gestion-calidad/seguridad-paciente?error={error}", status_code=303)
    return RedirectResponse(url=f"/gestion-calidad/seguridad-paciente/{evento_id}?guardado=1", status_code=303)


@router.get("/seguridad-paciente/{evento_id}", response_class=HTMLResponse)
async def ver_evento_seguridad(request: Request, evento_id: int, usuario=Depends(requiere_permiso("calidad"))):
    evento = ca.obtener_evento_seguridad(evento_id)
    if not evento:
        raise HTTPException(status_code=404, detail="El evento no existe.")
    return templates.TemplateResponse(
        request=request, name="calidad_avanzada/evento_seguridad_detalle.html",
        context={
            "usuario": usuario, "evento": evento,
            "guardado": request.query_params.get("guardado"), "error": request.query_params.get("error"),
        },
    )


@router.post("/seguridad-paciente/{evento_id}/analisis")
async def registrar_analisis_evento(
    evento_id: int, analisis: str = Form(...), causa_raiz: str = Form(""), plan_mejora: str = Form(""),
    usuario=Depends(requiere_permiso("calidad")),
):
    try:
        ca.registrar_analisis_evento(evento_id, analisis, causa_raiz, plan_mejora)
    except ValueError as error:
        return RedirectResponse(url=f"/gestion-calidad/seguridad-paciente/{evento_id}?error={error}", status_code=303)
    return RedirectResponse(url=f"/gestion-calidad/seguridad-paciente/{evento_id}?guardado=1", status_code=303)


@router.post("/seguridad-paciente/{evento_id}/cerrar")
async def cerrar_evento_seguridad(evento_id: int, seguimiento: str = Form(""), usuario=Depends(requiere_permiso("calidad"))):
    ca.cerrar_evento_seguridad(evento_id, seguimiento)
    return RedirectResponse(url=f"/gestion-calidad/seguridad-paciente/{evento_id}?guardado=1", status_code=303)


@router.post("/seguridad-paciente/{evento_id}/escalar")
async def escalar_evento_a_hallazgo(evento_id: int, usuario=Depends(requiere_permiso("calidad"))):
    try:
        hallazgo_id = ca.escalar_evento_a_hallazgo(evento_id, usuario_id=_id_usuario(usuario))
    except ValueError as error:
        return RedirectResponse(url=f"/gestion-calidad/seguridad-paciente/{evento_id}?error={error}", status_code=303)
    return RedirectResponse(url=f"/gestion-calidad/hallazgos/{hallazgo_id}?guardado=1", status_code=303)


# ==========================================================
# PQR / SIAU -- bandeja interna
# ==========================================================

from services import pqr_service as pqr


@router.get("/pqr", response_class=HTMLResponse)
async def bandeja_pqr(request: Request, usuario=Depends(requiere_permiso("calidad"))):
    filtro_estado = request.query_params.get("estado")
    filtro_riesgo = request.query_params.get("riesgo")
    filtro_vencidas = request.query_params.get("vencidas") == "1"
    return templates.TemplateResponse(
        request=request, name="calidad_avanzada/pqr_bandeja.html",
        context={
            "usuario": usuario, "pqrs": pqr.listar_bandeja(estado=filtro_estado, riesgo=filtro_riesgo, vencidas=filtro_vencidas),
            "indicadores": pqr.indicadores_pqr_siau(), "tipos": pqr.TIPOS_PQR, "canales": pqr.CANALES,
            "riesgos": pqr.RIESGOS, "estados": pqr.ESTADOS_PQR, "relaciones": pqr.RELACIONES_SOLICITANTE,
            "filtro_estado": filtro_estado, "filtro_riesgo": filtro_riesgo, "filtro_vencidas": filtro_vencidas,
            "guardado": request.query_params.get("guardado"), "error": request.query_params.get("error"),
        },
    )


@router.post("/pqr/crear")
async def crear_pqr_interna(request: Request, usuario=Depends(requiere_permiso("calidad"))):
    datos = dict(await request.form())
    try:
        resultado = pqr.radicar_pqr(datos, usuario_id=_id_usuario(usuario), es_publica=False)
    except ValueError as error:
        return RedirectResponse(url=f"/gestion-calidad/pqr?error={error}", status_code=303)
    return RedirectResponse(url=f"/gestion-calidad/pqr/{resultado['id']}?guardado=1", status_code=303)


@router.get("/pqr/{pqr_id}", response_class=HTMLResponse)
async def ver_pqr(request: Request, pqr_id: int, usuario=Depends(requiere_permiso("calidad"))):
    registro = pqr.obtener_pqr_completa(pqr_id)
    if not registro:
        raise HTTPException(status_code=404, detail="La PQR no existe.")
    return templates.TemplateResponse(
        request=request, name="calidad_avanzada/pqr_detalle.html",
        context={
            "usuario": usuario, "pqr": registro, "areas": pqr.AREAS_RESPONSABLES, "estados": pqr.ESTADOS_PQR,
            "guardado": request.query_params.get("guardado"), "error": request.query_params.get("error"),
        },
    )


@router.post("/pqr/{pqr_id}/asignar")
async def asignar_area_pqr(pqr_id: int, area_responsable: str = Form(...), usuario=Depends(requiere_permiso("calidad"))):
    try:
        pqr.asignar_area(pqr_id, area_responsable, usuario_id=_id_usuario(usuario))
    except ValueError as error:
        return RedirectResponse(url=f"/gestion-calidad/pqr/{pqr_id}?error={error}", status_code=303)
    return RedirectResponse(url=f"/gestion-calidad/pqr/{pqr_id}?guardado=1", status_code=303)


@router.post("/pqr/{pqr_id}/estado")
async def cambiar_estado_pqr_ruta(pqr_id: int, estado: str = Form(...), comentario: str = Form(""), usuario=Depends(requiere_permiso("calidad"))):
    try:
        pqr.cambiar_estado_pqr(pqr_id, estado, comentario, usuario_id=_id_usuario(usuario))
    except ValueError as error:
        return RedirectResponse(url=f"/gestion-calidad/pqr/{pqr_id}?error={error}", status_code=303)
    return RedirectResponse(url=f"/gestion-calidad/pqr/{pqr_id}?guardado=1", status_code=303)


@router.post("/pqr/{pqr_id}/comentario")
async def agregar_comentario_pqr(pqr_id: int, comentario: str = Form(...), usuario=Depends(requiere_permiso("calidad"))):
    try:
        pqr.agregar_comentario(pqr_id, comentario, usuario_id=_id_usuario(usuario))
    except ValueError as error:
        return RedirectResponse(url=f"/gestion-calidad/pqr/{pqr_id}?error={error}", status_code=303)
    return RedirectResponse(url=f"/gestion-calidad/pqr/{pqr_id}?guardado=1", status_code=303)


@router.post("/pqr/{pqr_id}/responder")
async def responder_pqr_ruta(pqr_id: int, respuesta: str = Form(...), medio_respuesta: str = Form(...), usuario=Depends(requiere_permiso("calidad"))):
    try:
        pqr.responder_pqr(pqr_id, respuesta, medio_respuesta, usuario_id=_id_usuario(usuario))
    except ValueError as error:
        return RedirectResponse(url=f"/gestion-calidad/pqr/{pqr_id}?error={error}", status_code=303)
    return RedirectResponse(url=f"/gestion-calidad/pqr/{pqr_id}?guardado=1", status_code=303)
