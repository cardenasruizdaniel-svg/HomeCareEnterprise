"""HomeCare Enterprise - Router: Administración del Portal Web Público"""

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse

from core.dependencies import requiere_permiso
from core.templates import templates

from services import configuracion_web_service as cw

router = APIRouter(prefix="/configuracion-web", tags=["Administración del Portal Web"])


def _id_usuario(usuario):
    return usuario.get("id") if isinstance(usuario, dict) else None


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def panel(request: Request, usuario=Depends(requiere_permiso("usuarios"))):
    return templates.TemplateResponse(
        request=request, name="configuracion_web/panel.html",
        context={
            "usuario": usuario, "config": cw.obtener_configuracion(), "servicios": cw.listar_servicios(),
            "iconos": cw.ICONOS_DISPONIBLES,
            "guardado": request.query_params.get("guardado"), "error": request.query_params.get("error"),
        },
    )


@router.post("/guardar")
async def guardar(request: Request, usuario=Depends(requiere_permiso("usuarios"))):
    datos = dict(await request.form())
    cw.guardar_configuracion(datos, usuario_id=_id_usuario(usuario))
    return RedirectResponse(url="/configuracion-web?guardado=1", status_code=303)


@router.post("/servicios/crear")
async def crear_servicio(request: Request, usuario=Depends(requiere_permiso("usuarios"))):
    datos = dict(await request.form())
    try:
        cw.crear_servicio(datos, usuario_id=_id_usuario(usuario))
    except ValueError as error:
        return RedirectResponse(url=f"/configuracion-web?error={error}", status_code=303)
    return RedirectResponse(url="/configuracion-web?guardado=1", status_code=303)


@router.post("/servicios/{servicio_id}/actualizar")
async def actualizar_servicio(request: Request, servicio_id: int, usuario=Depends(requiere_permiso("usuarios"))):
    datos = dict(await request.form())
    try:
        cw.actualizar_servicio(servicio_id, datos)
    except ValueError as error:
        return RedirectResponse(url=f"/configuracion-web?error={error}", status_code=303)
    return RedirectResponse(url="/configuracion-web?guardado=1", status_code=303)


@router.post("/servicios/{servicio_id}/desactivar")
async def desactivar_servicio(servicio_id: int, usuario=Depends(requiere_permiso("usuarios"))):
    cw.desactivar_servicio(servicio_id)
    return RedirectResponse(url="/configuracion-web?guardado=1", status_code=303)


@router.post("/servicios/{servicio_id}/reactivar")
async def reactivar_servicio(servicio_id: int, usuario=Depends(requiere_permiso("usuarios"))):
    cw.reactivar_servicio(servicio_id)
    return RedirectResponse(url="/configuracion-web?guardado=1", status_code=303)


@router.post("/imagen/{campo}")
async def subir_imagen(campo: str, archivo: UploadFile = File(...), usuario=Depends(requiere_permiso("usuarios"))):
    contenido = await archivo.read()
    try:
        cw.guardar_imagen_portal(campo, archivo.filename, contenido)
    except ValueError as error:
        return RedirectResponse(url=f"/configuracion-web?error={error}", status_code=303)
    return RedirectResponse(url="/configuracion-web?guardado=1", status_code=303)
