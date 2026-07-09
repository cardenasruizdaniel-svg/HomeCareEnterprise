"""HomeCare Enterprise - Router: Documentos del profesional"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.dependencies import requiere_permiso
from core.templates import templates
from database.database import consultar_uno

from services import documentos_profesional_service as docs_service

router = APIRouter(prefix="/documentos-profesional", tags=["Documentos del Profesional"])


@router.get("/{profesional_id}", response_class=HTMLResponse)
async def listado(request: Request, profesional_id: int, usuario=Depends(requiere_permiso("profesionales"))):
    profesional = consultar_uno("SELECT * FROM profesionales WHERE id=?", (profesional_id,))
    return templates.TemplateResponse(
        request=request, name="documentos_profesional/lista.html",
        context={
            "usuario": usuario, "profesional": profesional, "profesional_id": profesional_id,
            "documentos": docs_service.listar_por_profesional(profesional_id),
            "tipos": docs_service.TIPOS_DOCUMENTO,
        },
    )


@router.post("/guardar")
async def guardar(
    profesional_id: int = Form(...),
    tipo_documento: str = Form(...),
    nombre: str = Form(""),
    numero: str = Form(""),
    entidad_emisora: str = Form(""),
    fecha_expedicion: str = Form(""),
    fecha_vencimiento: str = Form(""),
    observaciones: str = Form(""),
    usuario=Depends(requiere_permiso("profesionales")),
):
    docs_service.crear(
        profesional_id, tipo_documento, nombre, numero, entidad_emisora,
        fecha_expedicion, fecha_vencimiento, None, observaciones,
        usuario.get("id") if isinstance(usuario, dict) else None,
    )
    return RedirectResponse(url=f"/documentos-profesional/{profesional_id}", status_code=303)


@router.get("/eliminar/{id}/{profesional_id}")
async def eliminar(id: int, profesional_id: int, _actor=Depends(requiere_permiso("profesionales"))):
    docs_service.eliminar(id)
    return RedirectResponse(url=f"/documentos-profesional/{profesional_id}", status_code=303)
