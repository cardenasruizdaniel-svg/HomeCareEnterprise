"""
=========================================================
HomeCare Enterprise
Router: Nomina

Permite CONSULTAR (sin comprometer nada) cuanto hay que
pagarle a cada profesional segun el tiempo real trabajado
en un periodo, y luego GENERAR la nomina formal para dejar
ese periodo liquidado.
=========================================================
"""

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.dependencies import requiere_permiso
from core.templates import templates

from services import nomina_service

router = APIRouter(prefix="/nomina", tags=["Nómina"])


# ==========================================
# PANEL PRINCIPAL
# ==========================================

@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def panel(
    request: Request,
    usuario=Depends(requiere_permiso("nomina")),
):
    nominas = nomina_service.listar_nominas()

    return templates.TemplateResponse(
        request=request,
        name="nomina/index.html",
        context={
            "usuario": usuario,
            "nominas": nominas,
        },
    )


# ==========================================
# CONSULTAR (previsualizar sin generar)
# ==========================================

@router.post("/consultar", response_class=HTMLResponse)
async def consultar(
    request: Request,
    fecha_inicio: str = Form(...),
    fecha_fin: str = Form(...),
    usuario=Depends(requiere_permiso("nomina")),
):
    previsualizacion = nomina_service.previsualizar_periodo(fecha_inicio, fecha_fin)
    nominas = nomina_service.listar_nominas()

    return templates.TemplateResponse(
        request=request,
        name="nomina/index.html",
        context={
            "usuario": usuario,
            "nominas": nominas,
            "previsualizacion": previsualizacion,
        },
    )


# ==========================================
# GENERAR (deja la nómina liquidada)
# ==========================================

@router.post("/generar")
async def generar(
    request: Request,
    fecha_inicio: str = Form(...),
    fecha_fin: str = Form(...),
    usuario=Depends(requiere_permiso("nomina")),
):
    try:
        nomina_id = nomina_service.generar_nomina(
            fecha_inicio, fecha_fin,
            usuario.get("id") if isinstance(usuario, dict) else None,
        )
    except ValueError as error:
        nominas = nomina_service.listar_nominas()
        return templates.TemplateResponse(
            request=request,
            name="nomina/index.html",
            context={
                "usuario": usuario,
                "nominas": nominas,
                "error": str(error),
            },
        )

    return RedirectResponse(url=f"/nomina/detalle/{nomina_id}", status_code=303)


# ==========================================
# DETALLE DE UNA NÓMINA GENERADA
# ==========================================

@router.get("/detalle/{nomina_id}", response_class=HTMLResponse)
async def detalle(
    request: Request,
    nomina_id: int,
    usuario=Depends(requiere_permiso("nomina")),
):
    try:
        datos = nomina_service.obtener_nomina_completa(nomina_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))

    from services import nomina_electronica_service
    dsne = nomina_electronica_service.listar_dsne_de_nomina(nomina_id)

    return templates.TemplateResponse(
        request=request,
        name="nomina/detalle.html",
        context={
            "usuario": usuario,
            "nomina": datos["nomina"],
            "detalle": datos["detalle"],
            "dsne": [dict(d) for d in dsne],
        },
    )


# ==========================================
# MARCAR UN PAGO COMO REALIZADO
# ==========================================

@router.get("/pagar/{detalle_id}/{nomina_id}")
async def pagar(
    detalle_id: int,
    nomina_id: int,
    _actor=Depends(requiere_permiso("nomina")),
):
    nomina_service.marcar_pagado(detalle_id)
    return RedirectResponse(url=f"/nomina/detalle/{nomina_id}", status_code=303)


# ==========================================
# NÓMINA ELECTRÓNICA (DSNE)
# ==========================================

@router.get("/electronica/{nomina_id}")
async def generar_electronica(
    nomina_id: int,
    usuario=Depends(requiere_permiso("nomina")),
):
    from services import nomina_electronica_service
    nomina_electronica_service.generar_dsne_nomina(
        nomina_id, usuario.get("id") if isinstance(usuario, dict) else None
    )
    return RedirectResponse(url=f"/nomina/detalle/{nomina_id}", status_code=303)
