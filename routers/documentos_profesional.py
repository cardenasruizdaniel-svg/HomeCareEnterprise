"""HomeCare Enterprise - Router: Documentos del profesional"""

from fastapi import APIRouter, Depends, Form, HTTPException, Request
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
    archivo_base64: str = Form(""),
    nombre_archivo: str = Form(""),
    usuario=Depends(requiere_permiso("profesionales")),
):
    docs_service.crear(
        profesional_id, tipo_documento, nombre, numero, entidad_emisora,
        fecha_expedicion, fecha_vencimiento, None, observaciones,
        usuario.get("id") if isinstance(usuario, dict) else None,
        archivo_base64=archivo_base64 or None, nombre_archivo=nombre_archivo or None,
    )
    return RedirectResponse(url=f"/documentos-profesional/{profesional_id}", status_code=303)


@router.get("/ver-archivo/{documento_id}")
async def ver_archivo(documento_id: int, usuario=Depends(requiere_permiso("profesionales"))):
    """
    Muestra/descarga el archivo (PDF o imagen) subido como
    soporte del documento -- ej. la foto o el escaneo del
    título profesional, la tarjeta profesional, etc.
    """
    documento = docs_service.obtener(documento_id)
    documento = dict(documento) if documento else {}

    if not documento.get("archivo_base64"):
        raise HTTPException(status_code=404, detail="Este documento no tiene ningún archivo adjunto.")

    import base64
    from fastapi.responses import Response

    encabezado, datos_b64 = documento["archivo_base64"].split(",", 1) if "," in documento["archivo_base64"] else ("", documento["archivo_base64"])
    tipo_mime = "application/pdf"
    if "image/" in encabezado:
        tipo_mime = encabezado.split(";")[0].replace("data:", "")

    contenido = base64.b64decode(datos_b64)
    nombre_descarga = documento.get("nombre_archivo") or "documento"

    return Response(
        content=contenido, media_type=tipo_mime,
        headers={"Content-Disposition": f'inline; filename="{nombre_descarga}"'},
    )


@router.get("/eliminar/{id}/{profesional_id}")
async def eliminar(id: int, profesional_id: int, _actor=Depends(requiere_permiso("profesionales"))):
    docs_service.eliminar(id)
    return RedirectResponse(url=f"/documentos-profesional/{profesional_id}", status_code=303)
