"""HomeCare Enterprise - Router: Copagos"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.dependencies import requiere_permiso
from core.templates import templates
from database.database import consultar_uno

from services import copagos_service

router = APIRouter(prefix="/copagos", tags=["Copagos"])


@router.get("/{paciente_id}", response_class=HTMLResponse)
async def listado(request: Request, paciente_id: int, usuario=Depends(requiere_permiso("facturacion"))):
    paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (paciente_id,))
    return templates.TemplateResponse(
        request=request, name="copagos/lista.html",
        context={
            "usuario": usuario, "paciente": paciente, "paciente_id": paciente_id,
            "copagos": copagos_service.listar_por_paciente(paciente_id),
        },
    )


@router.post("/guardar")
async def guardar(
    request: Request,
    paciente_id: int = Form(...),
    valor_copago: float = Form(...),
    concepto: str = Form(""),
    observaciones: str = Form(""),
    usuario=Depends(requiere_permiso("facturacion")),
):
    try:
        copagos_service.crear_copago(
            paciente_id, valor_copago, concepto, observaciones=observaciones,
            usuario=usuario.get("id") if isinstance(usuario, dict) else None,
        )
    except ValueError as error:
        paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (paciente_id,))
        return templates.TemplateResponse(
            request=request, name="copagos/lista.html",
            context={
                "usuario": usuario, "paciente": paciente, "paciente_id": paciente_id,
                "copagos": copagos_service.listar_por_paciente(paciente_id),
                "error": str(error),
            },
        )

    return RedirectResponse(url=f"/copagos/{paciente_id}", status_code=303)


@router.get("/marcar-pagado/{copago_id}/{paciente_id}")
async def marcar_pagado_form(request: Request, copago_id: int, paciente_id: int, usuario=Depends(requiere_permiso("facturacion"))):
    return templates.TemplateResponse(
        request=request, name="copagos/marcar_pago.html",
        context={"usuario": usuario, "copago_id": copago_id, "paciente_id": paciente_id},
    )


@router.post("/marcar-pagado/{copago_id}/{paciente_id}")
async def marcar_pagado(
    copago_id: int,
    paciente_id: int,
    metodo_pago: str = Form(...),
    generar_factura: bool = Form(False),
    usuario=Depends(requiere_permiso("facturacion")),
):
    copagos_service.marcar_pagado(copago_id, metodo_pago)

    if generar_factura:
        from services.facturacion_service import generar_factura_copago
        generar_factura_copago(copago_id, metodo_pago, usuario.get("id") if isinstance(usuario, dict) else None)

    return RedirectResponse(url=f"/copagos/{paciente_id}", status_code=303)
