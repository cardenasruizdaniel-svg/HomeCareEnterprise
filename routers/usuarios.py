"""
=========================================================
HomeCare Enterprise
Router: Usuarios (gestion de perfiles del sistema)
Reconstruido: el archivo original estaba corrupto
(sin router, sin imports, llamaba funciones inexistentes).
=========================================================
"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.dependencies import requiere_permiso
from core.roles import listar_roles_activos
from core.templates import templates

from services.usuarios_service import (
    actualizar_usuario,
    crear_usuario,
    eliminar_usuario,
    listar_usuarios,
    obtener_usuario,
)

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


# ==========================================
# LISTADO
# ==========================================

@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def listado(
    request: Request,
    usuario=Depends(requiere_permiso("usuarios")),
):
    usuarios = listar_usuarios()

    return templates.TemplateResponse(
        request=request,
        name="usuarios/lista.html",
        context={
            "usuario": usuario,
            "usuarios": usuarios,
            "roles": listar_roles_activos(),
        },
    )


# ==========================================
# NUEVO
# ==========================================

@router.get("/nuevo", response_class=HTMLResponse)
async def nuevo(
    request: Request,
    usuario=Depends(requiere_permiso("usuarios")),
):
    return templates.TemplateResponse(
        request=request,
        name="usuarios/nuevo.html",
        context={
            "usuario": usuario,
            "roles": listar_roles_activos(),
        },
    )


# ==========================================
# GUARDAR
# ==========================================

@router.post("/guardar")
async def guardar(
    nombre: str = Form(...),
    usuario: str = Form(...),
    password: str = Form(...),
    rol: str = Form(...),
    correo: str = Form(""),
    telefono: str = Form(""),
    _actor=Depends(requiere_permiso("usuarios")),
):
    crear_usuario(nombre, usuario, password, rol, correo, telefono)

    return RedirectResponse(url="/usuarios", status_code=303)


# ==========================================
# EDITAR
# ==========================================

@router.get("/editar/{id}", response_class=HTMLResponse)
async def editar(
    request: Request,
    id: int,
    usuario=Depends(requiere_permiso("usuarios")),
):
    registro = obtener_usuario(id)

    return templates.TemplateResponse(
        request=request,
        name="usuarios/editar.html",
        context={
            "usuario": registro,
            "roles": listar_roles_activos(),
        },
    )


# ==========================================
# ACTUALIZAR
# ==========================================

@router.post("/actualizar")
async def actualizar(
    id: int = Form(...),
    nombre: str = Form(...),
    usuario: str = Form(...),
    rol: str = Form(...),
    correo: str = Form(""),
    telefono: str = Form(""),
    estado: str = Form("Activo"),
    password: str = Form(""),
    _actor=Depends(requiere_permiso("usuarios")),
):
    actualizar_usuario(id, nombre, usuario, rol, correo, telefono, estado, password or None)

    return RedirectResponse(url="/usuarios", status_code=303)


# ==========================================
# ELIMINAR (inactivar)
# ==========================================

@router.get("/eliminar/{id}")
async def eliminar(
    id: int,
    _actor=Depends(requiere_permiso("usuarios")),
):
    eliminar_usuario(id)

    return RedirectResponse(url="/usuarios", status_code=303)
