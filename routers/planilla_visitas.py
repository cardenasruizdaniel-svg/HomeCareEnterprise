"""HomeCare Enterprise - Router: Planilla de visitas"""

from fastapi import APIRouter, Body, Depends, Request
from fastapi.responses import HTMLResponse

from core.dependencies import requiere_permiso
from core.templates import templates
from database.database import consultar_uno

from services import planilla_visitas_service, servicios_paciente_service

router = APIRouter(prefix="/planilla-visitas", tags=["Planilla de Visitas"])


@router.get("/{servicio_id}", response_class=HTMLResponse)
async def ver_planilla(request: Request, servicio_id: int, usuario=Depends(requiere_permiso("pacientes"))):
    servicio = servicios_paciente_service.obtener(servicio_id)
    servicio = dict(servicio) if servicio else {}

    paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (servicio.get("paciente_id"),)) if servicio else None

    return templates.TemplateResponse(
        request=request, name="planilla_visitas/lista.html",
        context={
            "usuario": usuario, "servicio": servicio, "servicio_id": servicio_id,
            "paciente": paciente,
            "filas": planilla_visitas_service.listar_por_servicio(servicio_id),
        },
    )


@router.post("/firmar/{planilla_id}")
async def firmar(planilla_id: int, datos: dict = Body(...), usuario=Depends(requiere_permiso("pacientes"))):
    try:
        resultado = planilla_visitas_service.firmar_visita(
            planilla_id,
            firmante=datos.get("firmante"),
            nombre_acompanante=datos.get("nombre_acompanante", ""),
            firma_base64=datos.get("firma_base64"),
            foto_base64=datos.get("foto_base64"),
            latitud=datos.get("latitud"),
            longitud=datos.get("longitud"),
        )
        return resultado
    except ValueError as error:
        return {"ok": False, "error": str(error)}
