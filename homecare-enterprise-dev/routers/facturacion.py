"""HomeCare Enterprise - Router: Facturacion electronica"""

from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from core.dependencies import requiere_permiso
from core.templates import templates
from database.database import consultar_todos, consultar_uno

from services import facturacion_service

router = APIRouter(prefix="/facturacion", tags=["Facturación Electrónica"])


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, usuario=Depends(requiere_permiso("facturacion"))):
    """
    Página principal del módulo: el dashboard del proceso de
    facturación (cuánto se ha facturado, cuánto se ha cobrado,
    qué está pendiente/vencido, tendencia por mes, y qué hay
    por facturar todavía).
    """
    return templates.TemplateResponse(
        request=request, name="facturacion/dashboard.html",
        context={"usuario": usuario, **facturacion_service.dashboard_facturacion()},
    )


@router.get("/listado", response_class=HTMLResponse)
async def listado(request: Request, usuario=Depends(requiere_permiso("facturacion"))):
    return templates.TemplateResponse(
        request=request, name="facturacion/lista.html",
        context={"usuario": usuario, "facturas": facturacion_service.listar_todas()},
    )


@router.get("/pdf/{factura_id}")
async def descargar_pdf(factura_id: int, usuario=Depends(requiere_permiso("facturacion"))):
    factura = facturacion_service.obtener(factura_id)
    if not factura or not dict(factura).get("pdf_path"):
        raise HTTPException(status_code=404, detail="PDF no disponible.")
    ruta = dict(factura)["pdf_path"]
    if not Path(ruta).exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado.")
    return FileResponse(ruta, media_type="application/pdf")


@router.get("/xml/{factura_id}")
async def descargar_xml(factura_id: int, usuario=Depends(requiere_permiso("facturacion"))):
    factura = dict(facturacion_service.obtener(factura_id) or {})
    if not factura.get("xml_path") or not Path(factura["xml_path"]).exists():
        raise HTTPException(status_code=404, detail="XML no encontrado.")
    return FileResponse(factura["xml_path"], media_type="application/xml")


# ==========================================================
# CARTERA (cuentas por cobrar)
# ==========================================================

@router.get("/cartera", response_class=HTMLResponse)
async def cartera(request: Request, estado: str = "", usuario=Depends(requiere_permiso("facturacion"))):
    return templates.TemplateResponse(
        request=request, name="facturacion/cartera.html",
        context={
            "usuario": usuario, "estado_filtro": estado,
            "facturas": facturacion_service.listar_cartera(estado or None),
        },
    )


@router.post("/cartera/{factura_id}/marcar-pagada")
async def marcar_pagada(
    request: Request,
    factura_id: int,
    valor_pagado: float = Form(...),
    metodo_pago: str = Form("Transferencia"),
    fecha_pago: str = Form(""),
    usuario=Depends(requiere_permiso("facturacion")),
):
    try:
        facturacion_service.marcar_pagada(factura_id, valor_pagado, metodo_pago, fecha_pago or None)
    except ValueError as error:
        return RedirectResponse(url=f"/facturacion/cartera?error={error}", status_code=303)
    return RedirectResponse(url="/facturacion/cartera", status_code=303)


@router.post("/cartera/{factura_id}/anular")
async def anular(
    request: Request,
    factura_id: int,
    motivo: str = Form(...),
    usuario=Depends(requiere_permiso("facturacion")),
):
    try:
        facturacion_service.anular_factura(factura_id, motivo)
    except ValueError as error:
        return RedirectResponse(url=f"/facturacion/cartera?error={error}", status_code=303)
    return RedirectResponse(url="/facturacion/cartera", status_code=303)


# ==========================================================
# PENDIENTES DE FACTURAR (servicios ya prestados sin facturar)
# ==========================================================

@router.get("/pendientes-facturar", response_class=HTMLResponse)
async def pendientes_facturar(request: Request, usuario=Depends(requiere_permiso("facturacion"))):
    return templates.TemplateResponse(
        request=request, name="facturacion/pendientes_facturar.html",
        context={"usuario": usuario, "pendientes": facturacion_service.pendientes_facturar()},
    )


# ==========================================================
# FACTURAR UN SERVICIO/INFORME (no solo copagos)
# ==========================================================

@router.get("/facturar-servicio/{servicio_paciente_id}", response_class=HTMLResponse)
async def facturar_servicio_formulario(
    request: Request, servicio_paciente_id: int, usuario=Depends(requiere_permiso("facturacion"))
):
    servicio = consultar_uno("SELECT * FROM servicios_paciente WHERE id=?", (servicio_paciente_id,))
    if not servicio:
        raise HTTPException(status_code=404, detail="El servicio no existe.")
    servicio = dict(servicio)
    paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (servicio["paciente_id"],))

    return templates.TemplateResponse(
        request=request, name="facturacion/facturar_servicio.html",
        context={"usuario": usuario, "servicio": servicio, "paciente": dict(paciente) if paciente else {}},
    )


@router.post("/facturar-servicio/{servicio_paciente_id}")
async def facturar_servicio_guardar(
    request: Request,
    servicio_paciente_id: int,
    valor_servicio: float = Form(...),
    medio_pago: str = Form("Transferencia"),
    usuario=Depends(requiere_permiso("facturacion")),
):
    try:
        resultado = facturacion_service.generar_factura_servicio(
            servicio_paciente_id, valor_servicio, medio_pago,
            usuario.get("id") if isinstance(usuario, dict) else None,
        )
    except ValueError as error:
        servicio = dict(consultar_uno("SELECT * FROM servicios_paciente WHERE id=?", (servicio_paciente_id,)) or {})
        paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (servicio.get("paciente_id"),))
        return templates.TemplateResponse(
            request=request, name="facturacion/facturar_servicio.html",
            context={
                "usuario": usuario, "servicio": servicio, "paciente": dict(paciente) if paciente else {},
                "error": str(error),
            },
        )
    return RedirectResponse(url=f"/facturacion/listado?generada={resultado['numero_completo']}", status_code=303)


# ==========================================================
# REPORTES
# ==========================================================

@router.get("/reportes", response_class=HTMLResponse)
async def reportes(
    request: Request,
    fecha_desde: str = "",
    fecha_hasta: str = "",
    usuario=Depends(requiere_permiso("facturacion")),
):
    fd = fecha_desde or None
    fh = fecha_hasta or None

    return templates.TemplateResponse(
        request=request, name="facturacion/reportes.html",
        context={
            "usuario": usuario, "fecha_desde": fecha_desde, "fecha_hasta": fecha_hasta,
            "resumen": facturacion_service.resumen_general(fd, fh),
            "por_paciente": facturacion_service.reporte_por_paciente(fd, fh),
            "por_eps": facturacion_service.reporte_por_eps(fd, fh),
            "por_fecha": facturacion_service.reporte_por_fecha(fd, fh) if fd and fh else [],
        },
    )
