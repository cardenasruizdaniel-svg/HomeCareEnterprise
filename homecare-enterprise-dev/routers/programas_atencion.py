"""HomeCare Enterprise - Router: Programas de Atención"""

from fastapi import APIRouter, Body, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from core.dependencies import requiere_permiso
from core.templates import templates
from database.database import consultar_todos, consultar_uno

from services import programas_atencion_service
from repositories.catalogo_actividades_repository import CatalogoActividadesRepository

router = APIRouter(prefix="/programas-atencion", tags=["Programas de Atención"])


@router.get("/api/actividades", response_class=JSONResponse)
async def api_actividades(_actor=Depends(requiere_permiso("pacientes"))):
    return [dict(a) for a in CatalogoActividadesRepository.listar_activas()]


@router.post("/asignar-completo")
async def asignar_completo(datos: dict = Body(...), usuario=Depends(requiere_permiso("pacientes"))):
    try:
        resultado = programas_atencion_service.asignar_programa_con_actividades(
            int(datos["paciente_id"]), int(datos["programa_id"]),
            int(datos["profesional_id"]) if datos.get("profesional_id") else None,
            datos.get("motivo", ""), datos.get("actividades", []),
            usuario.get("id") if isinstance(usuario, dict) else None,
        )
        return resultado
    except Exception as error:
        return {"error": str(error)}


# ==========================================
# CATÁLOGO (administración de programas)
# ==========================================

@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def catalogo(request: Request, usuario=Depends(requiere_permiso("pacientes"))):
    return templates.TemplateResponse(
        request=request, name="programas_atencion/catalogo.html",
        context={
            "usuario": usuario,
            "programas": programas_atencion_service.listar_programas_activos(),
            "conteo": programas_atencion_service.conteo_pacientes_por_programa(),
        },
    )


@router.post("/crear")
async def crear(
    nombre: str = Form(...),
    tipo: str = Form(...),
    subtipo: str = Form(""),
    descripcion: str = Form(""),
    usuario=Depends(requiere_permiso("pacientes")),
):
    programas_atencion_service.crear_programa(
        nombre, tipo, subtipo, descripcion,
        usuario.get("id") if isinstance(usuario, dict) else None,
    )
    return RedirectResponse(url="/programas-atencion", status_code=303)


@router.get("/desactivar/{programa_id}")
async def desactivar(programa_id: int, _actor=Depends(requiere_permiso("pacientes"))):
    programas_atencion_service.desactivar_programa(programa_id)
    return RedirectResponse(url="/programas-atencion", status_code=303)


# ==========================================
# ASIGNACIÓN DEL PROGRAMA A UN PACIENTE
# ==========================================

@router.get("/paciente/{paciente_id}", response_class=HTMLResponse)
async def ver_asignacion(request: Request, paciente_id: int, usuario=Depends(requiere_permiso("pacientes"))):
    paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (paciente_id,))
    profesionales = [
        dict(p) for p in consultar_todos(
            "SELECT id, nombre_completo, especialidad_principal FROM profesionales "
            "WHERE estado='ACTIVO' ORDER BY nombre_completo"
        )
    ]

    return templates.TemplateResponse(
        request=request, name="programas_atencion/asignar.html",
        context={
            "usuario": usuario, "paciente": paciente, "paciente_id": paciente_id,
            "programas": programas_atencion_service.listar_programas_activos(),
            "profesionales": profesionales,
            "programa_actual": programas_atencion_service.programa_actual(paciente_id),
            "historial": programas_atencion_service.historial_programas(paciente_id),
        },
    )


@router.post("/asignar")
async def asignar(
    request: Request,
    paciente_id: int = Form(...),
    programa_id: int = Form(...),
    profesional_id: str = Form(""),
    motivo: str = Form(""),
    usuario=Depends(requiere_permiso("pacientes")),
):
    try:
        programas_atencion_service.asignar_programa(
            paciente_id, programa_id,
            int(profesional_id) if profesional_id else None,
            motivo, usuario.get("id") if isinstance(usuario, dict) else None,
        )
    except ValueError as error:
        paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (paciente_id,))
        profesionales = [
            dict(p) for p in consultar_todos(
                "SELECT id, nombre_completo, especialidad_principal FROM profesionales WHERE estado='ACTIVO' ORDER BY nombre_completo"
            )
        ]
        return templates.TemplateResponse(
            request=request, name="programas_atencion/asignar.html",
            context={
                "usuario": usuario, "paciente": paciente, "paciente_id": paciente_id,
                "programas": programas_atencion_service.listar_programas_activos(),
                "profesionales": profesionales,
                "programa_actual": programas_atencion_service.programa_actual(paciente_id),
                "historial": programas_atencion_service.historial_programas(paciente_id),
                "error": str(error),
            },
        )

    return RedirectResponse(url=f"/programas-atencion/paciente/{paciente_id}", status_code=303)
