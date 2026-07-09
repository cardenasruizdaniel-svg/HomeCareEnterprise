"""
=========================================================
HomeCare Enterprise
Router: RIPS (Resolucion 948 de 2026)
=========================================================
"""

from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse

from core.config import EXPORTS_DIR, RIPS_NIT_PRESTADOR
from core.dependencies import requiere_permiso
from core.templates import templates

from services.rips_service import RIPSService

router = APIRouter(prefix="/rips", tags=["RIPS"])


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def panel(
    request: Request,
    usuario=Depends(requiere_permiso("rips")),
):
    return templates.TemplateResponse(
        request=request,
        name="rips/index.html",
        context={
            "usuario": usuario,
            "nit_configurado": RIPS_NIT_PRESTADOR,
        },
    )


@router.post("/generar", response_class=HTMLResponse)
async def generar(
    request: Request,
    fecha_inicio: str = Form(...),
    fecha_fin: str = Form(...),
    numero_factura: str = Form(""),
    nit_prestador: str = Form(""),
    usuario=Depends(requiere_permiso("rips")),
):
    resultado = RIPSService.generar(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        numero_factura=numero_factura,
        nit_prestador=nit_prestador or None,
    )

    archivo = RIPSService.guardar_archivo(
        resultado["transaccion"], numero_factura
    )

    return templates.TemplateResponse(
        request=request,
        name="rips/index.html",
        context={
            "usuario": usuario,
            "nit_configurado": RIPS_NIT_PRESTADOR,
            "resultado": resultado,
            "archivo_generado": Path(archivo).name,
        },
    )


@router.get("/descargar")
async def descargar(
    ruta: str,
    usuario=Depends(requiere_permiso("rips")),
):
    # Solo se permite descargar archivos dentro de exports/rips,
    # identificados por su nombre (no se acepta una ruta arbitraria).
    carpeta = Path(EXPORTS_DIR) / "rips"
    archivo = carpeta / Path(ruta).name

    if not archivo.exists() or carpeta.resolve() not in archivo.resolve().parents:
        raise HTTPException(status_code=404, detail="Archivo no encontrado.")

    return FileResponse(
        archivo,
        media_type="application/json",
        filename=archivo.name,
    )
