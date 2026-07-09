"""
=========================================================
HomeCare Enterprise
Router: Alergias del paciente
Reconstruido: el archivo original estaba corrupto
(sin router, sin imports, llamaba funciones inexistentes).
=========================================================
"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.dependencies import requiere_permiso
from core.templates import templates

from services.alergias_service import (
    ESTADOS,
    SEVERIDADES,
    TIPOS_VALIDOS,
    actualizar_alergia,
    cambiar_estado_alergia,
    crear_alergia,
    eliminar_alergia,
    listar_alergias,
    obtener_alergia,
)

router = APIRouter(prefix="/alergias", tags=["Alergias"])


# ==========================================
# LISTADO POR PACIENTE
# ==========================================

@router.get("/{paciente_id}", response_class=HTMLResponse)
async def listado(
    request: Request,
    paciente_id: int,
    usuario=Depends(requiere_permiso("pacientes")),
):
    alergias = listar_alergias(paciente_id)

    return templates.TemplateResponse(
        request=request,
        name="alergias/lista.html",
        context={
            "usuario": usuario,
            "paciente_id": paciente_id,
            "alergias": alergias,
        },
    )


# ==========================================
# NUEVO
# ==========================================

@router.get("/nuevo/{paciente_id}", response_class=HTMLResponse)
async def nuevo(
    request: Request,
    paciente_id: int,
    usuario=Depends(requiere_permiso("pacientes")),
):
    return templates.TemplateResponse(
        request=request,
        name="alergias/form.html",
        context={
            "usuario": usuario,
            "paciente_id": paciente_id,
            "alergia": None,
            "tipos": TIPOS_VALIDOS,
            "severidades": SEVERIDADES,
            "estados": ESTADOS,
        },
    )


# ==========================================
# GUARDAR
# ==========================================

@router.post("/guardar")
async def guardar(
    request: Request,
    paciente_id: int = Form(...),
    tipo: str = Form(...),
    alergeno: str = Form(...),
    severidad: str = Form(...),
    estado: str = Form(...),
    reaccion: str = Form(""),
    observaciones: str = Form(""),
    fecha_diagnostico: str = Form(""),
    usuario=Depends(requiere_permiso("pacientes")),
):
    try:
        crear_alergia(
            paciente_id, tipo, alergeno, severidad, estado,
            reaccion, observaciones, fecha_diagnostico,
            usuario.get("id") if isinstance(usuario, dict) else None,
        )
    except Exception as error:
        return templates.TemplateResponse(
            request=request,
            name="alergias/form.html",
            context={
                "usuario": usuario,
                "paciente_id": paciente_id,
                "alergia": None,
                "tipos": TIPOS_VALIDOS,
                "severidades": SEVERIDADES,
                "estados": ESTADOS,
                "error": str(error),
            },
        )

    return RedirectResponse(url=f"/alergias/{paciente_id}", status_code=303)


# ==========================================
# EDITAR
# ==========================================

@router.get("/editar/{id}", response_class=HTMLResponse)
async def editar(
    request: Request,
    id: int,
    usuario=Depends(requiere_permiso("pacientes")),
):
    alergia = obtener_alergia(id)

    return templates.TemplateResponse(
        request=request,
        name="alergias/form.html",
        context={
            "usuario": usuario,
            "paciente_id": alergia["paciente_id"] if alergia else None,
            "alergia": alergia,
            "tipos": TIPOS_VALIDOS,
            "severidades": SEVERIDADES,
            "estados": ESTADOS,
        },
    )


@router.post("/editar/{id}")
async def actualizar(
    request: Request,
    id: int,
    paciente_id: int = Form(...),
    tipo: str = Form(...),
    alergeno: str = Form(...),
    severidad: str = Form(...),
    estado: str = Form(...),
    reaccion: str = Form(""),
    observaciones: str = Form(""),
    fecha_diagnostico: str = Form(""),
    usuario=Depends(requiere_permiso("pacientes")),
):
    try:
        actualizar_alergia(
            id, tipo, alergeno, severidad, estado,
            reaccion, observaciones, fecha_diagnostico,
            usuario.get("id") if isinstance(usuario, dict) else None,
        )
    except Exception as error:
        alergia = obtener_alergia(id)
        return templates.TemplateResponse(
            request=request,
            name="alergias/form.html",
            context={
                "usuario": usuario,
                "paciente_id": paciente_id,
                "alergia": alergia,
                "tipos": TIPOS_VALIDOS,
                "severidades": SEVERIDADES,
                "estados": ESTADOS,
                "error": str(error),
            },
        )

    return RedirectResponse(url=f"/alergias/{paciente_id}", status_code=303)


# ==========================================
# CAMBIAR ESTADO
# ==========================================

@router.get("/estado/{id}/{estado}/{paciente_id}")
async def cambiar_estado(
    id: int,
    estado: str,
    paciente_id: int,
    _actor=Depends(requiere_permiso("pacientes")),
):
    cambiar_estado_alergia(id, estado)
    return RedirectResponse(url=f"/alergias/{paciente_id}", status_code=303)


# ==========================================
# ELIMINAR
# ==========================================

@router.get("/eliminar/{id}/{paciente_id}")
async def eliminar(
    id: int,
    paciente_id: int,
    _actor=Depends(requiere_permiso("pacientes")),
):
    eliminar_alergia(id)
    return RedirectResponse(url=f"/alergias/{paciente_id}", status_code=303)
