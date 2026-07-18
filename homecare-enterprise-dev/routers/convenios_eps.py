"""HomeCare Enterprise - Router: Convenios EPS y Facturación por Plan"""

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.dependencies import requiere_permiso
from core.templates import templates
from database.database import consultar_todos

from services import convenios_eps_service as convenios

router = APIRouter(prefix="/convenios-eps", tags=["Convenios EPS"])


def _id_usuario(usuario):
    return usuario.get("id") if isinstance(usuario, dict) else None


@router.get("/manual-pdf")
async def descargar_manual(usuario=Depends(requiere_permiso("facturacion"))):
    from fastapi.responses import FileResponse
    from core.config import RECURSOS_DIR
    ruta = RECURSOS_DIR / "docs" / "manuales" / "Manual_Convenios_EPS_Facturacion.docx"
    return FileResponse(
        ruta,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename="Manual_Convenios_EPS_HomeCare.docx",
    )


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def lista_convenios(request: Request, usuario=Depends(requiere_permiso("facturacion"))):
    from services.programas_atencion_service import listar_programas_activos
    return templates.TemplateResponse(
        request=request, name="convenios_eps/lista.html",
        context={
            "usuario": usuario, "convenios": convenios.listar_convenios(),
            "programas_atencion": listar_programas_activos(),
        },
    )


@router.post("/crear")
async def crear_convenio(
    request: Request,
    eps: str = Form(...), nit_eps: str = Form(""), nombre_plan: str = Form(...),
    numero_convenio: str = Form(""), fecha_inicio: str = Form(""), fecha_fin: str = Form(""),
    observaciones: str = Form(""),
    usuario=Depends(requiere_permiso("facturacion")),
):
    try:
        convenio_id = convenios.crear_convenio(eps, nit_eps, nombre_plan, numero_convenio, fecha_inicio, fecha_fin, observaciones, _id_usuario(usuario))
    except ValueError as error:
        return RedirectResponse(url=f"/convenios-eps?error={error}", status_code=303)
    return RedirectResponse(url=f"/convenios-eps/{convenio_id}", status_code=303)


@router.get("/{convenio_id}", response_class=HTMLResponse)
async def ver_convenio(request: Request, convenio_id: int, usuario=Depends(requiere_permiso("facturacion"))):
    from services.programas_atencion_service import listar_programas_activos
    convenio = convenios.obtener_convenio(convenio_id)
    if not convenio:
        raise HTTPException(status_code=404, detail="El convenio no existe.")
    return templates.TemplateResponse(
        request=request, name="convenios_eps/detalle.html",
        context={
            "usuario": usuario, "convenio": convenio,
            "actividades_catalogo": convenios.listar_actividades_catalogo(),
            "programas_atencion": listar_programas_activos(),
            "error": request.query_params.get("error"), "guardado": request.query_params.get("guardado"),
        },
    )


@router.post("/{convenio_id}/actualizar")
async def actualizar_convenio(
    request: Request, convenio_id: int,
    eps: str = Form(...), nit_eps: str = Form(""), nombre_plan: str = Form(...),
    numero_convenio: str = Form(""), fecha_inicio: str = Form(""), fecha_fin: str = Form(""),
    estado: str = Form("Vigente"), observaciones: str = Form(""),
    usuario=Depends(requiere_permiso("facturacion")),
):
    convenios.actualizar_convenio(convenio_id, eps, nit_eps, nombre_plan, numero_convenio, fecha_inicio, fecha_fin, estado, observaciones)
    return RedirectResponse(url=f"/convenios-eps/{convenio_id}?guardado=1", status_code=303)


@router.post("/{convenio_id}/servicios/agregar")
async def agregar_servicio(
    request: Request, convenio_id: int,
    actividad_id: str = Form(...), grupo_tope: str = Form(""),
    limite_cantidad: str = Form(...), dias_ciclo: str = Form("30"),
    valor_normal: str = Form("0"), valor_adicional: str = Form("0"),
    usuario=Depends(requiere_permiso("facturacion")),
):
    try:
        convenios.agregar_servicio_convenio(convenio_id, actividad_id, grupo_tope, limite_cantidad, dias_ciclo, valor_normal, valor_adicional)
    except ValueError as error:
        return RedirectResponse(url=f"/convenios-eps/{convenio_id}?error={error}", status_code=303)
    return RedirectResponse(url=f"/convenios-eps/{convenio_id}?guardado=1", status_code=303)


@router.post("/servicios/{servicio_id}/quitar")
async def quitar_servicio(servicio_id: int, convenio_id: int = Form(...), usuario=Depends(requiere_permiso("facturacion"))):
    convenios.quitar_servicio_convenio(servicio_id)
    return RedirectResponse(url=f"/convenios-eps/{convenio_id}?guardado=1", status_code=303)


@router.get("/buscar-pacientes")
async def buscar_pacientes(q: str = "", usuario=Depends(requiere_permiso("facturacion"))):
    if not q or len(q) < 2:
        return []
    filas = consultar_todos(
        "SELECT id, documento, primer_nombre, primer_apellido, eps FROM pacientes "
        "WHERE (primer_nombre LIKE ? OR primer_apellido LIKE ? OR documento LIKE ?) AND UPPER(estado)='ACTIVO' LIMIT 10",
        (f"%{q}%", f"%{q}%", f"%{q}%"),
    )
    return [dict(f) for f in filas]


@router.post("/asignar-paciente")
async def asignar_paciente(
    request: Request,
    paciente_id: str = Form(...), convenio_id: str = Form(...), fecha_ingreso: str = Form(""),
    fecha_fin: str = Form(""),
    usuario=Depends(requiere_permiso("facturacion")),
):
    try:
        convenios.asignar_convenio_paciente(int(paciente_id), int(convenio_id), fecha_ingreso, _id_usuario(usuario), fecha_fin=fecha_fin or None)
    except ValueError as error:
        return RedirectResponse(url=f"/convenios-eps/{convenio_id}?error={error}", status_code=303)
    return RedirectResponse(url=f"/convenios-eps/{convenio_id}?guardado=1", status_code=303)


# ==========================================================
# FACTURACIÓN A LA EPS (generar facturas de lo pendiente)
# ==========================================================

@router.get("/facturacion/panel", response_class=HTMLResponse)
async def panel_facturacion(
    request: Request,
    fecha_desde: str = "", fecha_hasta: str = "", eps: str = "",
    usuario=Depends(requiere_permiso("facturacion")),
):
    from datetime import date, timedelta
    fecha_desde = fecha_desde or (date.today() - timedelta(days=30)).isoformat()
    fecha_hasta = fecha_hasta or date.today().isoformat()

    return templates.TemplateResponse(
        request=request, name="convenios_eps/facturacion.html",
        context={
            "usuario": usuario,
            "cuentas": convenios.listar_cuentas_pendientes(fecha_desde, fecha_hasta, eps or None),
            "resumen_eps": convenios.resumen_pendientes_por_eps(fecha_desde, fecha_hasta),
            "fecha_desde": fecha_desde, "fecha_hasta": fecha_hasta, "eps": eps,
            "epses_disponibles": sorted({c["eps"] for c in convenios.listar_convenios()}),
            "mensaje": request.query_params.get("mensaje"),
        },
    )


@router.post("/facturacion/generar")
async def generar_facturas(
    request: Request,
    fecha_desde: str = Form(...), fecha_hasta: str = Form(...), modo: str = Form(...), eps: str = Form(""),
    usuario=Depends(requiere_permiso("facturacion")),
):
    try:
        resultado = convenios.generar_facturacion_eps(fecha_desde, fecha_hasta, modo, eps or None, _id_usuario(usuario))
        mensaje = f"Se generaron {resultado.get('total_facturas', len(resultado.get('facturas_generadas', [])))} factura(s)."
    except ValueError as error:
        mensaje = f"Error: {error}"

    from urllib.parse import quote
    return RedirectResponse(
        url=f"/convenios-eps/facturacion/panel?fecha_desde={fecha_desde}&fecha_hasta={fecha_hasta}&eps={eps}&mensaje={quote(mensaje)}",
        status_code=303,
    )
