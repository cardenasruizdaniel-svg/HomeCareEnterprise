"""
=========================================================
HomeCare Enterprise
Router: Interoperabilidad (IHCE - Resolucion 866 de 2021 /
Resolucion 1888 de 2025 - Resumen Digital de Atencion en
Salud, HL7 FHIR R4)
=========================================================
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from core.dependencies import requiere_permiso
from core.interoperability.exceptions import ValidationError
from core.templates import templates

from database.database import consultar_todos

from services.interoperabilidad_service import InteroperabilidadService

router = APIRouter(prefix="/interoperabilidad", tags=["Interoperabilidad"])


# ==========================================
# PANEL
# ==========================================

@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def panel(
    request: Request,
    usuario=Depends(requiere_permiso("interoperabilidad")),
):
    pacientes = consultar_todos(
        "SELECT id, documento, primer_nombre, primer_apellido "
        "FROM pacientes ORDER BY primer_apellido LIMIT 200"
    )

    return templates.TemplateResponse(
        request=request,
        name="interoperabilidad/index.html",
        context={
            "usuario": usuario,
            "pacientes": pacientes,
        },
    )


# ==========================================
# RDA DE UN PACIENTE (Bundle FHIR R4)
# ==========================================

@router.get("/rda/{paciente_id}")
async def rda(
    paciente_id: int,
    usuario=Depends(requiere_permiso("interoperabilidad")),
):
    try:
        return JSONResponse(
            content=InteroperabilidadService.generar_rda(paciente_id)
        )
    except ValidationError as error:
        raise HTTPException(status_code=404, detail=str(error))


# ==========================================
# COMPLETITUD DEL CONJUNTO DE DATOS RELEVANTES
# ==========================================

@router.get("/completitud/{paciente_id}")
async def completitud(
    paciente_id: int,
    usuario=Depends(requiere_permiso("interoperabilidad")),
):
    try:
        return InteroperabilidadService.verificar_completitud(paciente_id)
    except ValidationError as error:
        raise HTTPException(status_code=404, detail=str(error))


# ==========================================
# COMPATIBILIDAD (endpoint previo)
# ==========================================

@router.post("/patient")
async def exportar(datos: dict):
    return InteroperabilidadService.exportar_paciente(datos)
