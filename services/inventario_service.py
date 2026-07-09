"""
HomeCare Enterprise - Inventario de Insumos Médicos

Maneja el catálogo de insumos, los proveedores, y los
movimientos de ENTRADA (compras recibidas de un proveedor) y
SALIDA (insumos entregados/usados en el tratamiento de un
paciente), calculando el stock actual de cada insumo como la
diferencia entre entradas y salidas.
"""

from repositories.inventario_repository import (
    InsumosRepository,
    InventarioMovimientosRepository,
    ProveedoresRepository,
)

CATEGORIAS_INSUMO = [
    "Curación", "Protección personal (EPP)", "Sueros y soluciones",
    "Medicamentos", "Sondas y catéteres", "Oxigenoterapia", "Aseo y desinfección", "Otro",
]


# ==========================================
# PROVEEDORES
# ==========================================

def listar_proveedores_activos():
    return [dict(p) for p in ProveedoresRepository.listar_activos()]


def listar_proveedores():
    return [dict(p) for p in ProveedoresRepository.listar_todos()]


def crear_proveedor(nombre, nit, contacto, telefono, correo, direccion) -> int:
    if not nombre:
        raise ValueError("El nombre del proveedor es obligatorio.")
    return ProveedoresRepository.crear({
        "nombre": nombre, "nit": nit or "", "contacto": contacto or "",
        "telefono": telefono or "", "correo": correo or "", "direccion": direccion or "",
    })


def desactivar_proveedor(proveedor_id: int):
    ProveedoresRepository.cambiar_estado(proveedor_id, "Inactivo")


# ==========================================
# INSUMOS (catálogo)
# ==========================================

def listar_insumos_con_stock():
    filas = [dict(i) for i in InsumosRepository.listar_con_stock()]
    for f in filas:
        f["stock_bajo"] = f["stock_actual"] < (f["stock_minimo"] or 0)
    return filas


def crear_insumo(nombre, categoria, unidad_medida, stock_minimo) -> int:
    if not nombre:
        raise ValueError("El nombre del insumo es obligatorio.")
    return InsumosRepository.crear({
        "nombre": nombre, "categoria": categoria or "Otro",
        "unidad_medida": unidad_medida or "Unidad", "stock_minimo": stock_minimo or 0,
    })


def desactivar_insumo(insumo_id: int):
    InsumosRepository.desactivar(insumo_id)


def obtener_insumo(insumo_id: int):
    return InsumosRepository.obtener(insumo_id)


def stock_actual(insumo_id: int) -> int:
    return InsumosRepository.stock_actual(insumo_id)


# ==========================================
# MOVIMIENTOS (entradas / salidas)
# ==========================================

def registrar_entrada(insumo_id, cantidad, proveedor_id, numero_factura, costo_unitario, motivo, usuario_id) -> int:
    """Compra recibida de un proveedor: aumenta el stock."""

    if not insumo_id or not cantidad or cantidad <= 0:
        raise ValueError("Debe indicar el insumo y una cantidad mayor a cero.")

    return InventarioMovimientosRepository.crear({
        "insumo_id": insumo_id, "tipo": "Entrada", "cantidad": cantidad,
        "proveedor_id": proveedor_id or None, "numero_factura": numero_factura or "",
        "costo_unitario": costo_unitario or None, "paciente_id": None, "profesional_id": None,
        "motivo": motivo or "Compra", "usuario_creacion": usuario_id,
    })


def registrar_salida(insumo_id, cantidad, paciente_id, profesional_id, motivo, usuario_id) -> int:
    """Insumo entregado/usado en el tratamiento de un paciente: disminuye el stock."""

    if not insumo_id or not cantidad or cantidad <= 0:
        raise ValueError("Debe indicar el insumo y una cantidad mayor a cero.")

    stock = stock_actual(insumo_id)
    if cantidad > stock:
        raise ValueError(f"No hay suficiente stock: disponible {stock}, solicitado {cantidad}.")

    return InventarioMovimientosRepository.crear({
        "insumo_id": insumo_id, "tipo": "Salida", "cantidad": cantidad,
        "proveedor_id": None, "numero_factura": "", "costo_unitario": None,
        "paciente_id": paciente_id or None, "profesional_id": profesional_id or None,
        "motivo": motivo or "Entrega para tratamiento", "usuario_creacion": usuario_id,
    })


def listar_movimientos_por_insumo(insumo_id: int):
    return [dict(m) for m in InventarioMovimientosRepository.listar_por_insumo(insumo_id)]


def listar_movimientos_por_paciente(paciente_id: int):
    return [dict(m) for m in InventarioMovimientosRepository.listar_por_paciente(paciente_id)]


def listar_movimientos_recientes(limite=200):
    return [dict(m) for m in InventarioMovimientosRepository.listar_todos(limite)]
