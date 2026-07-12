"""HomeCare Enterprise - Router: Roles y Permisos"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.dependencies import requiere_permiso
from core.templates import templates

from services import roles_service

router = APIRouter(prefix="/roles-permisos", tags=["Roles y Permisos"])


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def ver(request: Request, usuario=Depends(requiere_permiso("usuarios"))):
    return templates.TemplateResponse(
        request=request, name="roles/lista.html",
        context={
            "usuario": usuario,
            "roles": roles_service.listar_roles(),
            "catalogo_modulos": roles_service.CATALOGO_MODULOS,
            "error": request.query_params.get("error"),
            "guardado": request.query_params.get("guardado"),
        },
    )


@router.post("/crear")
async def crear(
    request: Request,
    nombre: str = Form(...),
    descripcion: str = Form(""),
    acceso_total: str = Form(""),
    modulos: list[str] = Form([]),
    usuario=Depends(requiere_permiso("usuarios")),
):
    try:
        roles_service.crear_rol(nombre, descripcion, bool(acceso_total), modulos)
    except ValueError as error:
        return RedirectResponse(url=f"/roles-permisos?error={error}", status_code=303)
    return RedirectResponse(url="/roles-permisos?guardado=1", status_code=303)


@router.post("/{rol_id}/actualizar")
async def actualizar(
    request: Request,
    rol_id: int,
    descripcion: str = Form(""),
    acceso_total: str = Form(""),
    modulos: list[str] = Form([]),
    usuario=Depends(requiere_permiso("usuarios")),
):
    try:
        roles_service.actualizar_permisos_rol(rol_id, descripcion, bool(acceso_total), modulos)
    except ValueError as error:
        return RedirectResponse(url=f"/roles-permisos?error={error}", status_code=303)
    return RedirectResponse(url="/roles-permisos?guardado=1", status_code=303)


@router.post("/{rol_id}/eliminar")
async def eliminar(rol_id: int, usuario=Depends(requiere_permiso("usuarios"))):
    try:
        roles_service.desactivar_rol(rol_id)
    except ValueError as error:
        return RedirectResponse(url=f"/roles-permisos?error={error}", status_code=303)
    return RedirectResponse(url="/roles-permisos?guardado=1", status_code=303)
