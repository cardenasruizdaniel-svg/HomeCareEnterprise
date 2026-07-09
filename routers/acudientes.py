"""
HomeCare Enterprise - Router: Acudientes

Reconstruido: el archivo original no tenia declarado el
router, le faltaban todos los imports (Request, templates,
Form, RedirectResponse, los servicios), usaba una funcion de
autenticacion que no existe (get_current_user), y no
registraba proteccion de permisos en ninguna ruta.
"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.dependencies import requiere_permiso
from core.templates import templates

from services.acudientes_service import (
    actualizar_acudiente,
    crear_acudiente,
    definir_principal,
    eliminar_acudiente,
    obtener_acudiente,
    obtener_acudientes,
)

router = APIRouter(prefix="/acudientes", tags=["Acudientes"])


# ==========================================
# LISTADO
# ==========================================

@router.get("/{paciente_id}", response_class=HTMLResponse)
async def listado(request: Request, paciente_id: int, usuario=Depends(requiere_permiso("pacientes"))):

    acudientes = obtener_acudientes(paciente_id)

    return templates.TemplateResponse(
        request=request,
        name="acudientes/listado.html",
        context={
            "usuario": usuario,
            "paciente_id": paciente_id,
            "acudientes": acudientes,
        },
    )


# ==========================================
# NUEVO
# ==========================================

@router.get("/nuevo/{paciente_id}", response_class=HTMLResponse)
async def nuevo(request: Request, paciente_id: int, usuario=Depends(requiere_permiso("pacientes"))):

    return templates.TemplateResponse(
        request=request,
        name="acudientes/nuevo.html",
        context={
            "usuario": usuario,
            "paciente_id": paciente_id,
        },
    )


# ==========================================
# GUARDAR
# ==========================================

@router.post("/guardar")
async def guardar(
    paciente_id: int = Form(...),
    nombre: str = Form(...),
    tipo_documento: str = Form(""),
    documento: str = Form(""),
    parentesco: str = Form(...),
    telefono_principal: str = Form(...),
    telefono_secundario: str = Form(""),
    correo: str = Form(""),
    direccion: str = Form(""),
    barrio: str = Form(""),
    municipio: str = Form(""),
    departamento: str = Form(""),
    ciudad: str = Form(""),
    ocupacion: str = Form(""),
    observaciones: str = Form(""),
    es_principal: int = Form(1),
    autoriza_decisiones: int = Form(0),
    recibe_informacion: int = Form(1),
    usuario=Depends(requiere_permiso("pacientes")),
):

    crear_acudiente(
        paciente_id, nombre, tipo_documento, documento, parentesco,
        telefono_principal, telefono_secundario, correo, direccion, barrio,
        municipio, departamento, ciudad, ocupacion, observaciones,
        es_principal, autoriza_decisiones, recibe_informacion,
    )

    return RedirectResponse(url=f"/acudientes/{paciente_id}", status_code=303)


# ==========================================
# EDITAR
# ==========================================

@router.get("/editar/{id}", response_class=HTMLResponse)
async def editar(request: Request, id: int, usuario=Depends(requiere_permiso("pacientes"))):

    acudiente = obtener_acudiente(id)
    acudiente_dict = dict(acudiente) if acudiente else {}

    return templates.TemplateResponse(
        request=request,
        name="acudientes/editar.html",
        context={
            "usuario": usuario,
            "acudiente": acudiente,
            "paciente_id": acudiente_dict.get("paciente_id"),
        },
    )


# ==========================================
# ACTUALIZAR
# ==========================================

@router.post("/actualizar")
async def actualizar(
    id: int = Form(...),
    paciente_id: int = Form(...),
    nombre: str = Form(...),
    tipo_documento: str = Form(""),
    documento: str = Form(""),
    parentesco: str = Form(...),
    telefono_principal: str = Form(...),
    telefono_secundario: str = Form(""),
    correo: str = Form(""),
    direccion: str = Form(""),
    barrio: str = Form(""),
    municipio: str = Form(""),
    departamento: str = Form(""),
    ciudad: str = Form(""),
    ocupacion: str = Form(""),
    observaciones: str = Form(""),
    es_principal: int = Form(1),
    autoriza_decisiones: int = Form(0),
    recibe_informacion: int = Form(1),
    usuario=Depends(requiere_permiso("pacientes")),
):

    actualizar_acudiente(
        id, nombre, tipo_documento, documento, parentesco,
        telefono_principal, telefono_secundario, correo, direccion, barrio,
        municipio, departamento, ciudad, ocupacion, observaciones,
        es_principal, autoriza_decisiones, recibe_informacion,
    )

    return RedirectResponse(url=f"/acudientes/{paciente_id}", status_code=303)


# ==========================================
# ELIMINAR
# ==========================================

@router.get("/eliminar/{id}/{paciente_id}")
async def eliminar(id: int, paciente_id: int, usuario=Depends(requiere_permiso("pacientes"))):

    eliminar_acudiente(id)

    return RedirectResponse(url=f"/acudientes/{paciente_id}", status_code=303)


# ==========================================
# DEFINIR COMO PRINCIPAL
# ==========================================

@router.get("/principal/{id}/{paciente_id}")
async def principal(id: int, paciente_id: int, usuario=Depends(requiere_permiso("pacientes"))):

    definir_principal(id, paciente_id)

    return RedirectResponse(url=f"/acudientes/{paciente_id}", status_code=303)
