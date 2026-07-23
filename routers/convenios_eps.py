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
    return templates.TemplateResponse(
        request=request, name="convenios_eps/lista.html",
        context={
            "usuario": usuario, "convenios": convenios.listar_convenios(),
            "programas_generales": convenios.programas_generales_activos(),
            "error": request.query_params.get("error"),
        },
    )


@router.get("/programas-generales", response_class=HTMLResponse)
async def ver_programas_generales(request: Request, usuario=Depends(requiere_permiso("facturacion"))):
    from services.programas_atencion_service import listar_programas_activos
    return templates.TemplateResponse(
        request=request, name="convenios_eps/programas_generales.html",
        context={
            "usuario": usuario, "programas": convenios.programas_generales_activos(),
            "programas_atencion": listar_programas_activos(),
            "actividades_catalogo": convenios.listar_actividades_catalogo(),
            "error": request.query_params.get("error"), "guardado": request.query_params.get("guardado"),
        },
    )


@router.post("/programas-generales/crear")
async def crear_programa_general(
    nombre: str = Form(...), valor_mensual: str = Form("0"), observaciones: str = Form(""),
    usuario=Depends(requiere_permiso("facturacion")),
):
    try:
        convenios.crear_programa_convenio(None, nombre, valor_mensual, observaciones, _id_usuario(usuario))
    except ValueError as error:
        return RedirectResponse(url=f"/convenios-eps/programas-generales?error={error}", status_code=303)
    return RedirectResponse(url="/convenios-eps/programas-generales?guardado=1", status_code=303)


@router.post("/crear")
async def crear_convenio(
    request: Request,
    eps: str = Form(...), nit_eps: str = Form(""),
    numero_convenio: str = Form(""), fecha_inicio: str = Form(""), fecha_fin: str = Form(""),
    observaciones: str = Form(""),
    usuario=Depends(requiere_permiso("facturacion")),
):
    try:
        convenio_id = convenios.crear_convenio(eps, nit_eps, "", numero_convenio, fecha_inicio, fecha_fin, observaciones, _id_usuario(usuario))
    except ValueError as error:
        return RedirectResponse(url=f"/convenios-eps?error={error}", status_code=303)
    return RedirectResponse(url=f"/convenios-eps/{convenio_id}", status_code=303)


@router.get("/{convenio_id}", response_class=HTMLResponse)
async def ver_convenio(request: Request, convenio_id: int, usuario=Depends(requiere_permiso("facturacion"))):
    from services.programas_atencion_service import listar_programas_activos
    from services.profesionales_service import activos

    convenio = convenios.obtener_convenio(convenio_id)
    if not convenio:
        raise HTTPException(status_code=404, detail="El convenio no existe.")
    return templates.TemplateResponse(
        request=request, name="convenios_eps/detalle.html",
        context={
            "usuario": usuario, "convenio": convenio,
            "actividades_catalogo": convenios.listar_actividades_catalogo(),
            "programas_atencion": listar_programas_activos(),
            "profesionales": [dict(p) for p in activos()],
            "error": request.query_params.get("error"), "guardado": request.query_params.get("guardado"),
        },
    )


@router.post("/{convenio_id}/actualizar")
async def actualizar_convenio(
    request: Request, convenio_id: int,
    eps: str = Form(...), nit_eps: str = Form(""),
    numero_convenio: str = Form(""), fecha_inicio: str = Form(""), fecha_fin: str = Form(""),
    estado: str = Form("Vigente"), observaciones: str = Form(""),
    usuario=Depends(requiere_permiso("facturacion")),
):
    convenio_actual = convenios.obtener_convenio(convenio_id)
    nombre_plan = convenio_actual["nombre_plan"] if convenio_actual else ""
    convenios.actualizar_convenio(convenio_id, eps, nit_eps, nombre_plan, numero_convenio, fecha_inicio, fecha_fin, estado, observaciones)
    return RedirectResponse(url=f"/convenios-eps/{convenio_id}?guardado=1", status_code=303)


# ==========================================================
# PROGRAMAS DENTRO DE UN CONVENIO
# ==========================================================

@router.post("/{convenio_id}/programas/crear")
async def crear_programa(
    request: Request, convenio_id: int,
    nombre: str = Form(...), valor_mensual: str = Form("0"), observaciones: str = Form(""),
    usuario=Depends(requiere_permiso("facturacion")),
):
    try:
        convenios.crear_programa_convenio(convenio_id, nombre, valor_mensual, observaciones, _id_usuario(usuario))
    except ValueError as error:
        return RedirectResponse(url=f"/convenios-eps/{convenio_id}?error={error}", status_code=303)
    return RedirectResponse(url=f"/convenios-eps/{convenio_id}?guardado=1", status_code=303)


def _redireccion_tras_programa(convenio_id, mensaje_query):
    """A la pantalla del convenio si el programa pertenece a uno, o a Programas Generales si no."""
    if convenio_id:
        return RedirectResponse(url=f"/convenios-eps/{convenio_id}{mensaje_query}", status_code=303)
    return RedirectResponse(url=f"/convenios-eps/programas-generales{mensaje_query}", status_code=303)


@router.post("/programas/{programa_convenio_id}/actualizar")
async def actualizar_programa(
    programa_convenio_id: int, convenio_id: str = Form(""),
    nombre: str = Form(...), valor_mensual: str = Form("0"), observaciones: str = Form(""),
    usuario=Depends(requiere_permiso("facturacion")),
):
    convenio_id = int(convenio_id) if convenio_id else None
    try:
        convenios.actualizar_programa_convenio(programa_convenio_id, nombre, valor_mensual, observaciones)
    except ValueError as error:
        return _redireccion_tras_programa(convenio_id, f"?error={error}")
    return _redireccion_tras_programa(convenio_id, "?guardado=1")


@router.post("/programas/{programa_convenio_id}/desactivar")
async def desactivar_programa(programa_convenio_id: int, convenio_id: str = Form(""), usuario=Depends(requiere_permiso("facturacion"))):
    convenio_id = int(convenio_id) if convenio_id else None
    convenios.desactivar_programa_convenio(programa_convenio_id)
    return _redireccion_tras_programa(convenio_id, "?guardado=1")


# ==========================================================
# SERVICIOS PARAMETRIZADOS DENTRO DE UN PROGRAMA
# ==========================================================

@router.post("/programas/{programa_convenio_id}/servicios/agregar")
async def agregar_servicio(
    request: Request, programa_convenio_id: int, convenio_id: str = Form(""),
    actividad_id: str = Form(...), grupo_tope: str = Form(""),
    limite_cantidad: str = Form(...), dias_ciclo: str = Form("30"),
    valor_normal: str = Form("0"), valor_adicional: str = Form("0"),
    usuario=Depends(requiere_permiso("facturacion")),
):
    convenio_id = int(convenio_id) if convenio_id else None
    try:
        convenios.agregar_servicio_programa(programa_convenio_id, actividad_id, grupo_tope, limite_cantidad, dias_ciclo, valor_normal, valor_adicional)
    except ValueError as error:
        return _redireccion_tras_programa(convenio_id, f"?error={error}")
    return _redireccion_tras_programa(convenio_id, "?guardado=1")


@router.post("/servicios/{servicio_id}/quitar")
async def quitar_servicio(servicio_id: int, convenio_id: str = Form(""), usuario=Depends(requiere_permiso("facturacion"))):
    convenio_id = int(convenio_id) if convenio_id else None
    convenios.quitar_servicio_convenio(servicio_id)
    return _redireccion_tras_programa(convenio_id, "?guardado=1")


# ==========================================================
# ASIGNACIÓN DEL PROGRAMA A UN PACIENTE
# ==========================================================

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
    paciente_id: str = Form(...), programa_convenio_id: str = Form(...), convenio_id: str = Form(...),
    fecha_ingreso: str = Form(""), fecha_fin: str = Form(""),
    autorizacion: str = Form(""), profesional_tratante_id: str = Form(""), medico_tratante_id: str = Form(""),
    usuario=Depends(requiere_permiso("facturacion")),
):
    try:
        convenios.asignar_convenio_paciente(
            int(paciente_id), int(programa_convenio_id), fecha_ingreso, _id_usuario(usuario),
            fecha_fin=fecha_fin or None, autorizacion=autorizacion or None,
            profesional_tratante_id=int(profesional_tratante_id) if profesional_tratante_id else None,
            medico_tratante_id=int(medico_tratante_id) if medico_tratante_id else None,
        )
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
