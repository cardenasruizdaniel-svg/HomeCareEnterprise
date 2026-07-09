"""
=========================================================
HomeCare Enterprise
Router: Antecedentes del paciente
Reconstruido: el archivo original estaba corrupto
(sin router, sin imports, llamaba funciones inexistentes).
=========================================================
"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.dependencies import requiere_permiso
from core.templates import templates

from services.antecedentes_service import (
    TIPOS_VALIDOS,
    actualizar_antecedente,
    crear_antecedente,
    eliminar_antecedente,
    listar_antecedentes,
    obtener_antecedente,
)

router = APIRouter(prefix="/antecedentes", tags=["Antecedentes"])


# ==========================================
# LISTADO POR PACIENTE
# ==========================================

@router.get("/{paciente_id}", response_class=HTMLResponse)
async def listado(
    request: Request,
    paciente_id: int,
    usuario=Depends(requiere_permiso("pacientes")),
):
    antecedentes = listar_antecedentes(paciente_id)

    return templates.TemplateResponse(
        request=request,
        name="antecedentes/lista.html",
        context={
            "usuario": usuario,
            "paciente_id": paciente_id,
            "antecedentes": antecedentes,
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
        name="antecedentes/form.html",
        context={
            "usuario": usuario,
            "paciente_id": paciente_id,
            "antecedente": None,
            "tipos": TIPOS_VALIDOS,
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
    descripcion: str = Form(...),
    observaciones: str = Form(""),
    usuario=Depends(requiere_permiso("pacientes")),
):
    try:
        crear_antecedente(
            paciente_id, tipo, descripcion, observaciones,
            usuario.get("id") if isinstance(usuario, dict) else None,
        )
    except Exception as error:
        return templates.TemplateResponse(
            request=request,
            name="antecedentes/form.html",
            context={
                "usuario": usuario,
                "paciente_id": paciente_id,
                "antecedente": None,
                "tipos": TIPOS_VALIDOS,
                "error": str(error),
            },
        )

    return RedirectResponse(url=f"/antecedentes/{paciente_id}", status_code=303)


# ==========================================
# EDITAR
# ==========================================

@router.get("/editar/{id}", response_class=HTMLResponse)
async def editar(
    request: Request,
    id: int,
    usuario=Depends(requiere_permiso("pacientes")),
):
    antecedente = obtener_antecedente(id)

    return templates.TemplateResponse(
        request=request,
        name="antecedentes/form.html",
        context={
            "usuario": usuario,
            "paciente_id": antecedente["paciente_id"] if antecedente else None,
            "antecedente": antecedente,
            "tipos": TIPOS_VALIDOS,
        },
    )


@router.post("/editar/{id}")
async def actualizar(
    request: Request,
    id: int,
    paciente_id: int = Form(...),
    tipo: str = Form(...),
    descripcion: str = Form(...),
    observaciones: str = Form(""),
    usuario=Depends(requiere_permiso("pacientes")),
):
    try:
        actualizar_antecedente(
            id, tipo, descripcion, observaciones,
            usuario.get("id") if isinstance(usuario, dict) else None,
        )
    except Exception as error:
        antecedente = obtener_antecedente(id)
        return templates.TemplateResponse(
            request=request,
            name="antecedentes/form.html",
            context={
                "usuario": usuario,
                "paciente_id": paciente_id,
                "antecedente": antecedente,
                "tipos": TIPOS_VALIDOS,
                "error": str(error),
            },
        )

    return RedirectResponse(url=f"/antecedentes/{paciente_id}", status_code=303)


# ==========================================
# ELIMINAR
# ==========================================

@router.get("/eliminar/{id}/{paciente_id}")
async def eliminar(
    id: int,
    paciente_id: int,
    _actor=Depends(requiere_permiso("pacientes")),
):
    eliminar_antecedente(id)
    return RedirectResponse(url=f"/antecedentes/{paciente_id}", status_code=303)
