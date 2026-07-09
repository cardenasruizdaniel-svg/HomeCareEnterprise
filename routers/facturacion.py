"""HomeCare Enterprise - Router: Facturacion electronica"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse

from core.dependencies import requiere_permiso
from core.templates import templates

from services import facturacion_service

router = APIRouter(prefix="/facturacion", tags=["Facturación Electrónica"])


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def listado(request: Request, usuario=Depends(requiere_permiso("facturacion"))):
    return templates.TemplateResponse(
        request=request, name="facturacion/lista.html",
        context={"usuario": usuario, "facturas": facturacion_service.listar_todas()},
    )


@router.get("/pdf/{factura_id}")
async def descargar_pdf(factura_id: int, usuario=Depends(requiere_permiso("facturacion"))):
    factura = facturacion_service.obtener(factura_id)
    if not factura or not dict(factura).get("pdf_path"):
        raise HTTPException(status_code=404, detail="PDF no disponible.")
    ruta = dict(factura)["pdf_path"]
    if not Path(ruta).exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado.")
    return FileResponse(ruta, media_type="application/pdf")


@router.get("/xml/{factura_id}")
async def descargar_xml(factura_id: int, usuario=Depends(requiere_permiso("facturacion"))):
    factura = dict(facturacion_service.obtener(factura_id) or {})
    if not factura.get("xml_path") or not Path(factura["xml_path"]).exists():
        raise HTTPException(status_code=404, detail="XML no encontrado.")
    return FileResponse(factura["xml_path"], media_type="application/xml")
