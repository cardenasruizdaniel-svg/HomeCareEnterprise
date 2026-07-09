"""HomeCare Enterprise - Router: Inventario de Insumos Médicos"""

from fastapi import APIRouter, Depends, Form, Request
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
        },
    )


@router.post("/insumos/crear")
async def crear_insumo(
    nombre: str = Form(...),
    categoria: str = Form(""),
    unidad_medida: str = Form("Unidad"),
    stock_minimo: int = Form(0),
    usuario=Depends(requiere_permiso("inventario")),
):
    inventario_service.crear_insumo(nombre, categoria, unidad_medida, stock_minimo)
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
    usuario=Depends(requiere_permiso("inventario")),
):
    try:
        inventario_service.registrar_entrada(
            insumo_id, cantidad, int(proveedor_id) if proveedor_id else None,
            numero_factura, float(costo_unitario) if costo_unitario else None, motivo,
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
