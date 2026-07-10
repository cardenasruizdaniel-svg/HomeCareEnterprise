"""HomeCare Enterprise - Router: Módulo de Calidad"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.dependencies import requiere_permiso
from core.templates import templates
from database.database import consultar_todos

from services import calidad_service

router = APIRouter(prefix="/calidad", tags=["Calidad"])


def _contexto_base(usuario):
    profesionales = consultar_todos(
        "SELECT id, nombre_completo FROM profesionales WHERE estado='ACTIVO' ORDER BY nombre_completo"
    )
    pacientes = consultar_todos(
        "SELECT id, primer_nombre, primer_apellido, documento FROM pacientes ORDER BY primer_apellido"
    )
    return {
        "usuario": usuario, "profesionales": profesionales, "pacientes": pacientes,
        "tipos_pqr": calidad_service.TIPOS_PQR, "estados_pqr": calidad_service.ESTADOS_PQR,
        "prioridades": calidad_service.PRIORIDADES, "estados_planificacion": calidad_service.ESTADOS_PLANIFICACION,
        "dashboard": calidad_service.dashboard_calidad(),
    }


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def panel(request: Request, usuario=Depends(requiere_permiso("calidad"))):
    return templates.TemplateResponse(
        request=request, name="calidad/panel.html",
        context={
            **_contexto_base(usuario),
            "lista_pqr": calidad_service.listar_pqr(),
            "lista_planificacion": calidad_service.listar_planificacion(),
            "lista_evaluaciones": calidad_service.listar_evaluaciones(),
        },
    )


# ==========================================================
# PQR
# ==========================================================

@router.post("/pqr/crear")
async def crear_pqr(
    tipo: str = Form("PQR"),
    paciente_id: str = Form(""),
    asunto: str = Form(...),
    descripcion: str = Form(""),
    prioridad: str = Form("Media"),
    responsable_id: str = Form(""),
    usuario=Depends(requiere_permiso("calidad")),
):
    calidad_service.crear_pqr(
        tipo, int(paciente_id) if paciente_id else None, asunto, descripcion, prioridad,
        int(responsable_id) if responsable_id else None,
        usuario.get("id") if isinstance(usuario, dict) else None,
    )
    return RedirectResponse(url="/calidad#pqr", status_code=303)


@router.post("/pqr/{pqr_id}/estado")
async def cambiar_estado_pqr(
    pqr_id: int,
    estado: str = Form(...),
    respuesta: str = Form(""),
    _actor=Depends(requiere_permiso("calidad")),
):
    calidad_service.actualizar_estado_pqr(pqr_id, estado, respuesta or None)
    return RedirectResponse(url="/calidad#pqr", status_code=303)


# ==========================================================
# PLANIFICACIÓN DE TRABAJO
# ==========================================================

@router.post("/planificacion/crear")
async def crear_planificacion(
    titulo: str = Form(...),
    descripcion: str = Form(""),
    responsable_id: str = Form(""),
    fecha_inicio: str = Form(""),
    fecha_limite: str = Form(""),
    prioridad: str = Form("Media"),
    usuario=Depends(requiere_permiso("calidad")),
):
    calidad_service.crear_planificacion(
        titulo, descripcion, int(responsable_id) if responsable_id else None,
        fecha_inicio, fecha_limite, prioridad,
        usuario.get("id") if isinstance(usuario, dict) else None,
    )
    return RedirectResponse(url="/calidad#planificacion", status_code=303)


@router.post("/planificacion/{planificacion_id}/estado")
async def cambiar_estado_planificacion(
    planificacion_id: int,
    estado: str = Form(...),
    _actor=Depends(requiere_permiso("calidad")),
):
    calidad_service.actualizar_estado_planificacion(planificacion_id, estado)
    return RedirectResponse(url="/calidad#planificacion", status_code=303)


# ==========================================================
# EVALUACIÓN DE LA ATENCIÓN
# ==========================================================

@router.post("/evaluacion/crear")
async def crear_evaluacion(
    paciente_id: int = Form(...),
    profesional_id: str = Form(""),
    calificacion: int = Form(...),
    aspectos_evaluados: str = Form(""),
    comentario: str = Form(""),
    usuario=Depends(requiere_permiso("calidad")),
):
    calidad_service.crear_evaluacion(
        paciente_id, int(profesional_id) if profesional_id else None, calificacion,
        aspectos_evaluados, comentario,
        usuario.get("id") if isinstance(usuario, dict) else None,
    )
    return RedirectResponse(url="/calidad#evaluaciones", status_code=303)
