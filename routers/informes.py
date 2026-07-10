"""HomeCare Enterprise - Router: Módulo de Informes"""

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse, HTMLResponse

from core.config import EXPORTS_DIR
from core.dependencies import requiere_permiso
from core.templates import templates
from core.zonas import ZONAS_CIUDAD

from services import informes_service

router = APIRouter(prefix="/informes", tags=["Informes"])


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def panel(request: Request, usuario=Depends(requiere_permiso("pacientes"))):
    return templates.TemplateResponse(
        request=request, name="informes/panel.html",
        context={"usuario": usuario},
    )


@router.get("/caracterizacion-pacientes", response_class=HTMLResponse)
async def caracterizacion_pacientes(
    request: Request, zona: str = "", tipo_cuidado: str = "",
    usuario=Depends(requiere_permiso("pacientes")),
):
    pacientes = informes_service.caracterizacion_pacientes(zona or None, tipo_cuidado or None)
    return templates.TemplateResponse(
        request=request, name="informes/caracterizacion_pacientes.html",
        context={
            "usuario": usuario, "pacientes": pacientes, "zona": zona, "tipo_cuidado": tipo_cuidado,
            "zonas_ciudad": ZONAS_CIUDAD, "total": len(pacientes),
        },
    )


@router.get("/caracterizacion-pacientes/excel")
async def caracterizacion_pacientes_excel(
    zona: str = "", tipo_cuidado: str = "",
    usuario=Depends(requiere_permiso("pacientes")),
):
    from services.informes_excel_service import generar_excel_caracterizacion
    pacientes = informes_service.caracterizacion_pacientes(zona or None, tipo_cuidado or None)
    ruta = generar_excel_caracterizacion(pacientes)
    return FileResponse(
        ruta, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=Path(ruta).name,
    )


@router.get("/resumen-zonas", response_class=HTMLResponse)
async def resumen_zonas(request: Request, usuario=Depends(requiere_permiso("pacientes"))):
    return templates.TemplateResponse(
        request=request, name="informes/resumen_zonas.html",
        context={
            "usuario": usuario,
            "por_zona": informes_service.resumen_por_zona(),
            "por_municipio": informes_service.resumen_por_municipio(),
            "por_eps": informes_service.resumen_por_eps(),
        },
    )


@router.get("/resumen-zonas/excel")
async def resumen_zonas_excel(usuario=Depends(requiere_permiso("pacientes"))):
    from services.informes_excel_service import generar_excel_resumen_zonas
    ruta = generar_excel_resumen_zonas(
        informes_service.resumen_por_zona(),
        informes_service.resumen_por_municipio(),
        informes_service.resumen_por_eps(),
    )
    return FileResponse(
        ruta, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=Path(ruta).name,
    )


@router.get("/equipo-profesional", response_class=HTMLResponse)
async def equipo_profesional(request: Request, usuario=Depends(requiere_permiso("profesionales"))):
    return templates.TemplateResponse(
        request=request, name="informes/equipo_profesional.html",
        context={"usuario": usuario, "profesionales": informes_service.equipo_profesional()},
    )


@router.get("/equipo-profesional/excel")
async def equipo_profesional_excel(usuario=Depends(requiere_permiso("profesionales"))):
    from services.informes_excel_service import generar_excel_equipo_profesional
    ruta = generar_excel_equipo_profesional(informes_service.equipo_profesional())
    return FileResponse(
        ruta, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=Path(ruta).name,
    )
