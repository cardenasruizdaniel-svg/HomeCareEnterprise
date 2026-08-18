"""HomeCare Enterprise - Router: Auditoría del Sistema"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from core.dependencies import requiere_gerencia_o_admin
from core.templates import templates

from services import auditoria_service as auditoria

router = APIRouter(prefix="/auditoria", tags=["Auditoría"])


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def panel(
    request: Request,
    fecha_desde: str = "", fecha_hasta: str = "",
    usuario_id: str = "", modulo: str = "", resultado: str = "",
    usuario=Depends(requiere_gerencia_o_admin()),
):
    from datetime import date, timedelta
    fecha_desde = fecha_desde or (date.today() - timedelta(days=7)).isoformat()
    fecha_hasta = fecha_hasta or date.today().isoformat()

    registros = auditoria.listar(
        fecha_desde=fecha_desde, fecha_hasta=fecha_hasta,
        usuario_id=int(usuario_id) if usuario_id else None,
        modulo=modulo or None, resultado=resultado or None,
    )

    return templates.TemplateResponse(
        request=request, name="auditoria/panel.html",
        context={
            "usuario": usuario,
            "registros": registros,
            "resumen": auditoria.resumen_dashboard(24),
            "resumen_usuarios": auditoria.resumen_por_usuario(fecha_desde, fecha_hasta),
            "modulos_disponibles": auditoria.listar_modulos_con_actividad(),
            "fecha_desde": fecha_desde, "fecha_hasta": fecha_hasta,
            "filtro_usuario_id": usuario_id, "filtro_modulo": modulo, "filtro_resultado": resultado,
        },
    )


@router.get("/usuario/{usuario_id}", response_class=HTMLResponse)
async def historial_usuario(request: Request, usuario_id: int, usuario=Depends(requiere_gerencia_o_admin())):
    registros = auditoria.historial_usuario(usuario_id)
    nombre_usuario = registros[0]["usuario"] if registros else None
    return templates.TemplateResponse(
        request=request, name="auditoria/historial_usuario.html",
        context={"usuario": usuario, "registros": registros, "usuario_id": usuario_id, "nombre_usuario": nombre_usuario},
    )
