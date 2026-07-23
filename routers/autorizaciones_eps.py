"""HomeCare Enterprise - Router: Autorizaciones de Servicios Adicionales (EPS)"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.dependencies import requiere_permiso
from core.templates import templates

from services import autorizaciones_eps_service as autorizaciones

router = APIRouter(prefix="/autorizaciones-eps", tags=["Autorizaciones EPS"])


def _id_usuario(usuario):
    return usuario.get("id") if isinstance(usuario, dict) else None


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def panel_autorizaciones(request: Request, estado: str = "", usuario=Depends(requiere_permiso("facturacion"))):
    return templates.TemplateResponse(
        request=request, name="autorizaciones_eps/panel.html",
        context={
            "usuario": usuario,
            "solicitudes": autorizaciones.listar_solicitudes(estado or None),
            "resumen": autorizaciones.resumen_dashboard(),
            "estado_filtro": estado,
            "mensaje": request.query_params.get("mensaje"),
            "error": request.query_params.get("error"),
        },
    )


@router.post("/{solicitud_id}/autorizar")
async def autorizar(
    solicitud_id: int,
    numero_autorizacion: str = Form(...), fecha_autorizacion: str = Form(""),
    cantidad_autorizada: str = Form(...), valor_autorizado: str = Form("0"),
    observaciones: str = Form(""),
    usuario=Depends(requiere_permiso("facturacion")),
):
    try:
        autorizaciones.autorizar_solicitud(
            solicitud_id, numero_autorizacion, fecha_autorizacion, cantidad_autorizada,
            valor_autorizado, None, observaciones, _id_usuario(usuario),
        )
        mensaje = "Solicitud autorizada correctamente. Ya se puede programar la cantidad autorizada."
        return RedirectResponse(url=f"/autorizaciones-eps?mensaje={mensaje}", status_code=303)
    except ValueError as error:
        return RedirectResponse(url=f"/autorizaciones-eps?error={error}", status_code=303)


@router.post("/{solicitud_id}/rechazar")
async def rechazar(solicitud_id: int, observaciones: str = Form(""), usuario=Depends(requiere_permiso("facturacion"))):
    autorizaciones.rechazar_solicitud(solicitud_id, observaciones, _id_usuario(usuario))
    return RedirectResponse(url="/autorizaciones-eps?mensaje=Solicitud rechazada.", status_code=303)
