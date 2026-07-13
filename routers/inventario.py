"""HomeCare Enterprise - Router: Inventario de Insumos Médicos"""

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from core.dependencies import requiere_permiso
from core.templates import templates
from database.database import consultar_todos

from services import inventario_service

router = APIRouter(prefix="/inventario", tags=["Inventario"])


@router.get("/api/proveedores-activos", response_class=JSONResponse)
async def api_proveedores_activos(_actor=Depends(requiere_permiso("inventario"))):
    return inventario_service.listar_proveedores_activos()


# ==========================================
# DASHBOARD / LISTADO DE INSUMOS CON STOCK
# ==========================================

@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, usuario=Depends(requiere_permiso("inventario"))):
    return templates.TemplateResponse(
        request=request, name="inventario/dashboard.html",
        context={
            "usuario": usuario,
            "insumos": inventario_service.listar_insumos_con_stock(),
            "movimientos_recientes": inventario_service.listar_movimientos_recientes(30),
            "categorias": inventario_service.CATEGORIAS_INSUMO,
            "resumen": inventario_service.resumen_dashboard(),
            "alertas_vencimiento": inventario_service.alertas_vencimiento(90),
        },
    )


@router.post("/insumos/crear")
async def crear_insumo(
    nombre: str = Form(...),
    categoria: str = Form(""),
    unidad_medida: str = Form("Unidad"),
    stock_minimo: int = Form(0),
    stock_maximo: int = Form(0),
    codigo: str = Form(""),
    requiere_lote_vencimiento: str = Form(""),
    usuario=Depends(requiere_permiso("inventario")),
):
    inventario_service.crear_insumo(
        nombre, categoria, unidad_medida, stock_minimo,
        codigo=codigo, stock_maximo=stock_maximo, requiere_lote_vencimiento=bool(requiere_lote_vencimiento),
    )
    return RedirectResponse(url="/inventario", status_code=303)


@router.get("/insumos/desactivar/{insumo_id}")
async def desactivar_insumo(insumo_id: int, _actor=Depends(requiere_permiso("inventario"))):
    inventario_service.desactivar_insumo(insumo_id)
    return RedirectResponse(url="/inventario", status_code=303)


# ==========================================
# MOVIMIENTOS: ENTRADA (compra) / SALIDA (entrega)
# ==========================================

@router.post("/entrada")
async def registrar_entrada(
    request: Request,
    insumo_id: int = Form(...),
    cantidad: int = Form(...),
    proveedor_id: str = Form(""),
    numero_factura: str = Form(""),
    costo_unitario: str = Form(""),
    motivo: str = Form(""),
    lote: str = Form(""),
    fecha_vencimiento: str = Form(""),
    usuario=Depends(requiere_permiso("inventario")),
):
    try:
        inventario_service.registrar_entrada(
            insumo_id, cantidad, int(proveedor_id) if proveedor_id else None,
            numero_factura, float(costo_unitario) if costo_unitario else None, motivo,
            usuario.get("id") if isinstance(usuario, dict) else None,
            lote=lote or None, fecha_vencimiento=fecha_vencimiento or None,
        )
    except ValueError as error:
        return templates.TemplateResponse(
            request=request, name="inventario/dashboard.html",
            context={
                "usuario": usuario,
                "insumos": inventario_service.listar_insumos_con_stock(),
                "movimientos_recientes": inventario_service.listar_movimientos_recientes(30),
                "categorias": inventario_service.CATEGORIAS_INSUMO,
                "resumen": inventario_service.resumen_dashboard(),
                "alertas_vencimiento": inventario_service.alertas_vencimiento(90),
                "error": str(error),
            },
        )
    return RedirectResponse(url="/inventario", status_code=303)


@router.post("/salida")
async def registrar_salida(
    request: Request,
    insumo_id: int = Form(...),
    cantidad: int = Form(...),
    paciente_id: str = Form(""),
    profesional_id: str = Form(""),
    motivo: str = Form(""),
    usuario=Depends(requiere_permiso("inventario")),
):
    try:
        inventario_service.registrar_salida(
            insumo_id, cantidad, int(paciente_id) if paciente_id else None,
            int(profesional_id) if profesional_id else None, motivo,
            usuario.get("id") if isinstance(usuario, dict) else None,
        )
    except ValueError as error:
        return templates.TemplateResponse(
            request=request, name="inventario/dashboard.html",
            context={
                "usuario": usuario,
                "insumos": inventario_service.listar_insumos_con_stock(),
                "movimientos_recientes": inventario_service.listar_movimientos_recientes(30),
                "categorias": inventario_service.CATEGORIAS_INSUMO,
                "resumen": inventario_service.resumen_dashboard(),
                "alertas_vencimiento": inventario_service.alertas_vencimiento(90),
                "error": str(error),
            },
        )
    return RedirectResponse(url="/inventario", status_code=303)


@router.get("/movimientos/{insumo_id}", response_class=HTMLResponse)
async def movimientos_insumo(request: Request, insumo_id: int, usuario=Depends(requiere_permiso("inventario"))):
    insumo = inventario_service.obtener_insumo(insumo_id)

    return templates.TemplateResponse(
        request=request, name="inventario/movimientos.html",
        context={
            "usuario": usuario, "insumo": insumo,
            "movimientos": inventario_service.listar_movimientos_por_insumo(insumo_id),
            "stock_actual": inventario_service.stock_actual(insumo_id),
        },
    )


# ==========================================
# PROVEEDORES
# ==========================================

@router.get("/proveedores", response_class=HTMLResponse)
async def proveedores(request: Request, usuario=Depends(requiere_permiso("inventario"))):
    return templates.TemplateResponse(
        request=request, name="inventario/proveedores.html",
        context={"usuario": usuario, "proveedores": inventario_service.listar_proveedores()},
    )


@router.post("/proveedores/crear")
async def crear_proveedor(
    nombre: str = Form(...),
    nit: str = Form(""),
    contacto: str = Form(""),
    telefono: str = Form(""),
    correo: str = Form(""),
    direccion: str = Form(""),
    usuario=Depends(requiere_permiso("inventario")),
):
    inventario_service.crear_proveedor(nombre, nit, contacto, telefono, correo, direccion)
    return RedirectResponse(url="/inventario/proveedores", status_code=303)


@router.get("/proveedores/desactivar/{proveedor_id}")
async def desactivar_proveedor(proveedor_id: int, _actor=Depends(requiere_permiso("inventario"))):
    inventario_service.desactivar_proveedor(proveedor_id)
    return RedirectResponse(url="/inventario/proveedores", status_code=303)


# ==========================================
# INSUMOS ENTREGADOS A UN PACIENTE (para ver
# desde su ficha)
# ==========================================

@router.get("/paciente/{paciente_id}", response_class=HTMLResponse)
async def insumos_paciente(request: Request, paciente_id: int, usuario=Depends(requiere_permiso("inventario"))):
    from database.database import consultar_uno
    paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (paciente_id,))
    profesionales = consultar_todos(
        "SELECT id, nombre_completo FROM profesionales WHERE estado='ACTIVO' ORDER BY nombre_completo"
    )

    return templates.TemplateResponse(
        request=request, name="inventario/insumos_paciente.html",
        context={
            "usuario": usuario, "paciente": paciente, "paciente_id": paciente_id,
            "movimientos": inventario_service.listar_movimientos_por_paciente(paciente_id),
            "insumos": inventario_service.listar_insumos_con_stock(),
            "profesionales": profesionales,
        },
    )


@router.post("/paciente/{paciente_id}/entregar")
async def entregar_insumo_paciente(
    request: Request,
    paciente_id: int,
    insumo_id: int = Form(...),
    cantidad: int = Form(...),
    profesional_id: str = Form(""),
    motivo: str = Form(""),
    usuario=Depends(requiere_permiso("inventario")),
):
    from database.database import consultar_uno
    paciente = consultar_uno("SELECT * FROM pacientes WHERE id=?", (paciente_id,))
    profesionales = consultar_todos(
        "SELECT id, nombre_completo FROM profesionales WHERE estado='ACTIVO' ORDER BY nombre_completo"
    )

    contexto_base = {
        "usuario": usuario, "paciente": paciente, "paciente_id": paciente_id,
        "insumos": inventario_service.listar_insumos_con_stock(),
        "profesionales": profesionales,
    }

    try:
        inventario_service.registrar_salida(
            insumo_id, cantidad, paciente_id,
            int(profesional_id) if profesional_id else None, motivo,
            usuario.get("id") if isinstance(usuario, dict) else None,
        )
    except ValueError as error:
        return templates.TemplateResponse(
            request=request, name="inventario/insumos_paciente.html",
            context={
                **contexto_base,
                "movimientos": inventario_service.listar_movimientos_por_paciente(paciente_id),
                "error": str(error),
            },
        )

    return templates.TemplateResponse(
        request=request, name="inventario/insumos_paciente.html",
        context={
            **contexto_base,
            "movimientos": inventario_service.listar_movimientos_por_paciente(paciente_id),
            "entregado": True,
        },
    )


# ==========================================
# INFORMES PROFESIONALES
# ==========================================

@router.get("/informes/existencias", response_class=HTMLResponse)
async def informe_existencias(request: Request, usuario=Depends(requiere_permiso("inventario"))):
    return templates.TemplateResponse(
        request=request, name="inventario/informe_existencias.html",
        context={"usuario": usuario, "informe": inventario_service.informe_existencias()},
    )


@router.get("/informes/existencias/pdf")
async def informe_existencias_pdf(usuario=Depends(requiere_permiso("inventario"))):
    from fastapi.responses import FileResponse
    from services.configuracion_empresa_service import obtener as obtener_config_empresa
    config = obtener_config_empresa()
    ruta = inventario_service_pdf().generar_pdf_existencias(
        inventario_service.informe_existencias(), config.get("razon_social", "")
    )
    return FileResponse(ruta, media_type="application/pdf", filename="informe_existencias.pdf")


@router.get("/informes/compras", response_class=HTMLResponse)
async def informe_compras(
    request: Request,
    fecha_desde: str = "",
    fecha_hasta: str = "",
    proveedor_id: str = "",
    usuario=Depends(requiere_permiso("inventario")),
):
    from datetime import date, timedelta
    fecha_desde = fecha_desde or (date.today() - timedelta(days=30)).isoformat()
    fecha_hasta = fecha_hasta or date.today().isoformat()
    return templates.TemplateResponse(
        request=request, name="inventario/informe_compras.html",
        context={
            "usuario": usuario,
            "informe": inventario_service.informe_compras(fecha_desde, fecha_hasta, int(proveedor_id) if proveedor_id else None),
            "fecha_desde": fecha_desde, "fecha_hasta": fecha_hasta, "proveedor_id": proveedor_id,
            "proveedores": inventario_service.listar_proveedores_activos(),
        },
    )


@router.get("/informes/compras/pdf")
async def informe_compras_pdf(
    fecha_desde: str, fecha_hasta: str, proveedor_id: str = "",
    usuario=Depends(requiere_permiso("inventario")),
):
    from fastapi.responses import FileResponse
    from services.configuracion_empresa_service import obtener as obtener_config_empresa
    config = obtener_config_empresa()
    informe = inventario_service.informe_compras(fecha_desde, fecha_hasta, int(proveedor_id) if proveedor_id else None)
    ruta = inventario_service_pdf().generar_pdf_compras(informe, fecha_desde, fecha_hasta, config.get("razon_social", ""))
    return FileResponse(ruta, media_type="application/pdf", filename="informe_compras.pdf")


@router.get("/informes/movimientos", response_class=HTMLResponse)
async def informe_movimientos(
    request: Request,
    fecha_desde: str = "",
    fecha_hasta: str = "",
    insumo_id: str = "",
    tipo: str = "",
    usuario=Depends(requiere_permiso("inventario")),
):
    from datetime import date, timedelta
    fecha_desde = fecha_desde or (date.today() - timedelta(days=30)).isoformat()
    fecha_hasta = fecha_hasta or date.today().isoformat()
    return templates.TemplateResponse(
        request=request, name="inventario/informe_movimientos.html",
        context={
            "usuario": usuario,
            "informe": inventario_service.informe_movimientos(
                fecha_desde, fecha_hasta, int(insumo_id) if insumo_id else None, tipo or None
            ),
            "fecha_desde": fecha_desde, "fecha_hasta": fecha_hasta, "insumo_id": insumo_id, "tipo": tipo,
            "insumos": inventario_service.listar_insumos_con_stock(),
        },
    )


@router.get("/informes/movimientos/pdf")
async def informe_movimientos_pdf(
    fecha_desde: str, fecha_hasta: str, insumo_id: str = "", tipo: str = "",
    usuario=Depends(requiere_permiso("inventario")),
):
    from fastapi.responses import FileResponse
    from services.configuracion_empresa_service import obtener as obtener_config_empresa
    config = obtener_config_empresa()
    informe = inventario_service.informe_movimientos(fecha_desde, fecha_hasta, int(insumo_id) if insumo_id else None, tipo or None)
    ruta = inventario_service_pdf().generar_pdf_movimientos(informe, fecha_desde, fecha_hasta, config.get("razon_social", ""))
    return FileResponse(ruta, media_type="application/pdf", filename="informe_movimientos.pdf")


def inventario_service_pdf():
    from services import inventario_pdf_service
    return inventario_pdf_service


# ==========================================
# CONVENIOS CON PROVEEDORES
# ==========================================

@router.get("/convenios", response_class=HTMLResponse)
async def convenios(request: Request, usuario=Depends(requiere_permiso("inventario"))):
    return templates.TemplateResponse(
        request=request, name="inventario/convenios.html",
        context={
            "usuario": usuario, "convenios": inventario_service.listar_convenios(),
            "proveedores": inventario_service.listar_proveedores_activos(),
            "tipos_convenio": inventario_service.TIPOS_CONVENIO,
        },
    )


@router.post("/convenios/crear")
async def crear_convenio(
    request: Request,
    proveedor_id: int = Form(...),
    numero_convenio: str = Form(""),
    tipo: str = Form(...),
    fecha_inicio: str = Form(""),
    fecha_fin: str = Form(""),
    valor: str = Form(""),
    condiciones: str = Form(""),
    usuario=Depends(requiere_permiso("inventario")),
):
    try:
        inventario_service.crear_convenio(
            proveedor_id, numero_convenio, tipo, fecha_inicio or None, fecha_fin or None,
            float(valor) if valor else None, condiciones,
            usuario.get("id") if isinstance(usuario, dict) else None,
        )
    except ValueError as error:
        return templates.TemplateResponse(
            request=request, name="inventario/convenios.html",
            context={
                "usuario": usuario, "convenios": inventario_service.listar_convenios(),
                "proveedores": inventario_service.listar_proveedores_activos(),
                "tipos_convenio": inventario_service.TIPOS_CONVENIO, "error": str(error),
            },
        )
    return RedirectResponse(url="/inventario/convenios", status_code=303)


@router.post("/convenios/{convenio_id}/finalizar")
async def finalizar_convenio(convenio_id: int, usuario=Depends(requiere_permiso("inventario"))):
    inventario_service.finalizar_convenio(convenio_id)
    return RedirectResponse(url="/inventario/convenios", status_code=303)


@router.get("/convenios/{convenio_id}/pdf")
async def convenio_pdf(convenio_id: int, usuario=Depends(requiere_permiso("inventario"))):
    from fastapi.responses import FileResponse
    from services.configuracion_empresa_service import obtener as obtener_config_empresa
    convenio = inventario_service.obtener_convenio(convenio_id)
    if not convenio:
        raise HTTPException(status_code=404, detail="El convenio no existe.")
    config = obtener_config_empresa()
    ruta = inventario_service_pdf().generar_pdf_convenio(convenio, config.get("razon_social", ""), config.get("nit", ""))
    return FileResponse(ruta, media_type="application/pdf", filename=f"convenio_{convenio_id}.pdf")
