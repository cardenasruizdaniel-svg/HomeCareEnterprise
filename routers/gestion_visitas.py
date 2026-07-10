"""HomeCare Enterprise - Router: Gestión de Visitas (Programar/Cancelar/Reprogramar)"""

from fastapi import APIRouter, Body, Depends, Request
from fastapi.responses import HTMLResponse

from core.dependencies import requiere_permiso
from core.templates import templates
from database.database import consultar_todos, consultar_uno

from services import gestion_visitas_service, servicios_paciente_service

router = APIRouter(prefix="/gestion-visitas", tags=["Gestión de Visitas"])


@router.get("/{servicio_id}", response_class=HTMLResponse)
async def listado(request: Request, servicio_id: int, usuario=Depends(requiere_permiso("programacion"))):
    servicio = servicios_paciente_service.obtener(servicio_id)
    servicio = dict(servicio) if servicio else {}

    paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (servicio.get("paciente_id"),)) if servicio else None
    profesionales = consultar_todos(
        "SELECT id, nombre_completo, especialidad_principal FROM profesionales WHERE estado='ACTIVO' ORDER BY nombre_completo"
    )

    sugerencia_medicos = []
    es_servicio_medico = "édic" in (servicio.get("tipo_servicio") or "")
    if es_servicio_medico:
        from services.sugerencia_medico_service import sugerir_medicos
        sugerencia_medicos = sugerir_medicos()

    return templates.TemplateResponse(
        request=request, name="gestion_visitas/lista.html",
        context={
            "usuario": usuario, "servicio": servicio, "servicio_id": servicio_id,
            "paciente": paciente, "profesionales": profesionales,
            "visitas": gestion_visitas_service.listar_visitas_de_servicio(servicio_id),
            "es_servicio_medico": es_servicio_medico,
            "sugerencia_medicos": sugerencia_medicos,
        },
    )


@router.post("/programar/{planilla_id}")
async def programar(planilla_id: int, datos: dict = Body(...), usuario=Depends(requiere_permiso("programacion"))):
    try:
        resultado = gestion_visitas_service.programar_visita(
            planilla_id, datos.get("fecha"), datos.get("hora_inicio"), datos.get("hora_fin"),
            int(datos["profesional_id"]) if datos.get("profesional_id") else None,
            usuario.get("id") if isinstance(usuario, dict) else None,
        )
        return resultado
    except ValueError as error:
        return {"ok": False, "error": str(error)}


@router.post("/reprogramar/{planilla_id}")
async def reprogramar(planilla_id: int, datos: dict = Body(...), usuario=Depends(requiere_permiso("programacion"))):
    try:
        resultado = gestion_visitas_service.reprogramar_visita(
            planilla_id, datos.get("fecha"), datos.get("hora_inicio"), datos.get("hora_fin"),
            int(datos["profesional_id"]) if datos.get("profesional_id") else None,
            usuario.get("id") if isinstance(usuario, dict) else None,
        )
        return resultado
    except ValueError as error:
        return {"ok": False, "error": str(error)}


@router.post("/cancelar/{planilla_id}")
async def cancelar(planilla_id: int, datos: dict = Body(...), usuario=Depends(requiere_permiso("programacion"))):
    try:
        resultado = gestion_visitas_service.cancelar_visita(
            planilla_id, datos.get("motivo", ""),
            usuario.get("id") if isinstance(usuario, dict) else None,
        )
        return resultado
    except ValueError as error:
        return {"ok": False, "error": str(error)}
