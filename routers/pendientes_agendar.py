"""HomeCare Enterprise - Router: Pacientes Pendientes de Agendar"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from core.dependencies import requiere_permiso
from core.templates import templates

from services.pendientes_agendar_service import resumen_pendientes

router = APIRouter(prefix="/pendientes-agendar", tags=["Pendientes de Agendar"])


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def ver(request: Request, usuario=Depends(requiere_permiso("pacientes"))):
    return templates.TemplateResponse(
        request=request, name="pendientes_agendar/lista.html",
        context={"usuario": usuario, **resumen_pendientes()},
    )
