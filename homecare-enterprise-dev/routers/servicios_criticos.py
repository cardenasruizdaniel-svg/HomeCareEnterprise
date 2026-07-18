"""
HomeCare Enterprise - Router: Seguimiento de Servicios Críticos

Ventana dedicada para vigilar los servicios donde el horario
importa mucho -- aplicación de medicamentos, aplicación de
sueros, y toma de muestras de laboratorio -- mostrando qué está
programado hoy, qué está en curso, qué ya se completó, y una
alerta clara para lo que ya se pasó de hora sin haberse hecho.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from core.dependencies import requiere_permiso
from core.templates import templates

router = APIRouter(prefix="/servicios-criticos", tags=["Servicios Críticos"])


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def panel_servicios_criticos(request: Request, usuario=Depends(requiere_permiso("programacion"))):
    from services.dashboard_operativo_service import panel_servicios_criticos as obtener_panel
    return templates.TemplateResponse(
        request=request, name="servicios_criticos/panel.html",
        context={"usuario": usuario, "panel": obtener_panel()},
    )


@router.get("/datos")
async def datos_servicios_criticos(usuario=Depends(requiere_permiso("programacion"))):
    """Para refrescar el panel por AJAX sin recargar toda la página."""
    from services.dashboard_operativo_service import panel_servicios_criticos as obtener_panel
    return obtener_panel()
