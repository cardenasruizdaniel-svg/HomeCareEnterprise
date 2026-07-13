"""HomeCare Enterprise - Repositorio: Inventario de Insumos"""

from database.database import consultar_todos, consultar_uno, ejecutar


class ProveedoresRepository:

    @staticmethod
    def listar_activos():
        return consultar_todos("SELECT * FROM proveedores WHERE estado='Activo' ORDER BY nombre")

    @staticmethod
    def listar_todos():
        return consultar_todos("SELECT * FROM proveedores ORDER BY nombre")

    @staticmethod
    def obtener(proveedor_id: int):
        return consultar_uno("SELECT * FROM proveedores WHERE id=?", (proveedor_id,))

    @staticmethod
    def crear(datos: dict) -> int:
        return ejecutar(
            """
            INSERT INTO proveedores(nombre, nit, contacto, telefono, correo, direccion)
            VALUES (:nombre, :nit, :contacto, :telefono, :correo, :direccion)
            """,
            datos,
        )

    @staticmethod
    def cambiar_estado(proveedor_id: int, estado: str):
        ejecutar("UPDATE proveedores SET estado=? WHERE id=?", (estado, proveedor_id))


class InsumosRepository:

    @staticmethod
    def listar_activos():
        return consultar_todos("SELECT * FROM insumos WHERE activo=1 ORDER BY nombre")

    @staticmethod
    def obtener(insumo_id: int):
        return consultar_uno("SELECT * FROM insumos WHERE id=?", (insumo_id,))

    @staticmethod
    def crear(datos: dict) -> int:
        return ejecutar(
            """
            INSERT INTO insumos(codigo, nombre, categoria, unidad_medida, stock_minimo, stock_maximo, requiere_lote_vencimiento)
            VALUES (:codigo, :nombre, :categoria, :unidad_medida, :stock_minimo, :stock_maximo, :requiere_lote_vencimiento)
            """,
            datos,
        )

    @staticmethod
    def actualizar_costo_promedio(insumo_id: int, nuevo_costo_promedio: float):
        ejecutar("UPDATE insumos SET costo_promedio=? WHERE id=?", (nuevo_costo_promedio, insumo_id))

    @staticmethod
    def desactivar(insumo_id: int):
        ejecutar("UPDATE insumos SET activo=0 WHERE id=?", (insumo_id,))

    @staticmethod
    def stock_actual(insumo_id: int) -> int:
        fila = consultar_uno(
            """
            SELECT
                COALESCE(SUM(CASE WHEN tipo='Entrada' THEN cantidad ELSE 0 END), 0)
                - COALESCE(SUM(CASE WHEN tipo='Salida' THEN cantidad ELSE 0 END), 0) AS stock
            FROM inventario_movimientos WHERE insumo_id=?
            """,
            (insumo_id,),
        )
        return dict(fila)["stock"] if fila else 0

    @staticmethod
    def listar_con_stock():
        return consultar_todos(
            """
            SELECT i.*,
                COALESCE(SUM(CASE WHEN m.tipo='Entrada' THEN m.cantidad ELSE 0 END), 0)
                - COALESCE(SUM(CASE WHEN m.tipo='Salida' THEN m.cantidad ELSE 0 END), 0) AS stock_actual
            FROM insumos i
            LEFT JOIN inventario_movimientos m ON m.insumo_id = i.id
            WHERE i.activo=1
            GROUP BY i.id
            ORDER BY i.nombre
            """
        )


class InventarioMovimientosRepository:

    @staticmethod
    def crear(datos: dict) -> int:
        return ejecutar(
            """
            INSERT INTO inventario_movimientos(
                insumo_id, tipo, cantidad, proveedor_id, numero_factura, costo_unitario,
                paciente_id, profesional_id, motivo, lote, fecha_vencimiento, saldo_despues, usuario_creacion
            ) VALUES (
                :insumo_id, :tipo, :cantidad, :proveedor_id, :numero_factura, :costo_unitario,
                :paciente_id, :profesional_id, :motivo, :lote, :fecha_vencimiento, :saldo_despues, :usuario_creacion
            )
            """,
            datos,
        )

    @staticmethod
    def listar_por_insumo(insumo_id: int):
        return consultar_todos(
            """
            SELECT m.*, pr.nombre AS proveedor, pa.primer_nombre, pa.primer_apellido
            FROM inventario_movimientos m
            LEFT JOIN proveedores pr ON pr.id = m.proveedor_id
            LEFT JOIN pacientes pa ON pa.id = m.paciente_id
            WHERE m.insumo_id=?
            ORDER BY m.fecha DESC
            """,
            (insumo_id,),
        )

    @staticmethod
    def listar_por_paciente(paciente_id: int):
        return consultar_todos(
            """
            SELECT m.*, i.nombre AS insumo, i.unidad_medida
            FROM inventario_movimientos m
            JOIN insumos i ON i.id = m.insumo_id
            WHERE m.paciente_id=? AND m.tipo='Salida'
            ORDER BY m.fecha DESC
            """,
            (paciente_id,),
        )

    @staticmethod
    def listar_todos(limite=200):
        return consultar_todos(
            """
            SELECT m.*, i.nombre AS insumo, i.unidad_medida, pr.nombre AS proveedor
            FROM inventario_movimientos m
            JOIN insumos i ON i.id = m.insumo_id
            LEFT JOIN proveedores pr ON pr.id = m.proveedor_id
            ORDER BY m.fecha DESC
            LIMIT ?
            """,
            (limite,),
        )

    @staticmethod
    def informe_compras(fecha_desde: str, fecha_hasta: str, proveedor_id=None):
        sql = """
            SELECT m.*, i.nombre AS insumo, i.unidad_medida, i.codigo, pr.nombre AS proveedor, pr.nit AS proveedor_nit
            FROM inventario_movimientos m
            JOIN insumos i ON i.id = m.insumo_id
            LEFT JOIN proveedores pr ON pr.id = m.proveedor_id
            WHERE m.tipo='Entrada' AND date(m.fecha) BETWEEN date(?) AND date(?)
        """
        parametros = [fecha_desde, fecha_hasta]
        if proveedor_id:
            sql += " AND m.proveedor_id=?"
            parametros.append(proveedor_id)
        sql += " ORDER BY m.fecha DESC"
        return consultar_todos(sql, tuple(parametros))

    @staticmethod
    def informe_movimientos(fecha_desde: str, fecha_hasta: str, insumo_id=None, tipo=None):
        sql = """
            SELECT m.*, i.nombre AS insumo, i.unidad_medida, i.codigo,
                   pr.nombre AS proveedor, pa.primer_nombre, pa.primer_apellido
            FROM inventario_movimientos m
            JOIN insumos i ON i.id = m.insumo_id
            LEFT JOIN proveedores pr ON pr.id = m.proveedor_id
            LEFT JOIN pacientes pa ON pa.id = m.paciente_id
            WHERE date(m.fecha) BETWEEN date(?) AND date(?)
        """
        parametros = [fecha_desde, fecha_hasta]
        if insumo_id:
            sql += " AND m.insumo_id=?"
            parametros.append(insumo_id)
        if tipo:
            sql += " AND m.tipo=?"
            parametros.append(tipo)
        sql += " ORDER BY m.fecha ASC"
        return consultar_todos(sql, tuple(parametros))

    @staticmethod
    def lotes_por_vencer(dias: int):
        return consultar_todos(
            """
            SELECT m.*, i.nombre AS insumo, i.unidad_medida,
                   julianday(m.fecha_vencimiento) - julianday('now') AS dias_restantes
            FROM inventario_movimientos m
            JOIN insumos i ON i.id = m.insumo_id
            WHERE m.tipo='Entrada' AND m.fecha_vencimiento IS NOT NULL
              AND date(m.fecha_vencimiento) <= date('now', '+' || ? || ' days')
            ORDER BY m.fecha_vencimiento ASC
            """,
            (dias,),
        )


class ConveniosRepository:

    @staticmethod
    def listar_todos():
        return consultar_todos(
            """
            SELECT c.*, pr.nombre AS proveedor, pr.nit AS proveedor_nit
            FROM convenios c
            JOIN proveedores pr ON pr.id = c.proveedor_id
            ORDER BY c.fecha_creacion DESC
            """
        )

    @staticmethod
    def obtener(convenio_id: int):
        return consultar_uno(
            """
            SELECT c.*, pr.nombre AS proveedor, pr.nit AS proveedor_nit, pr.direccion AS proveedor_direccion,
                   pr.telefono AS proveedor_telefono, pr.correo AS proveedor_correo, pr.contacto AS proveedor_contacto
            FROM convenios c
            JOIN proveedores pr ON pr.id = c.proveedor_id
            WHERE c.id=?
            """,
            (convenio_id,),
        )

    @staticmethod
    def crear(datos: dict) -> int:
        return ejecutar(
            """
            INSERT INTO convenios(proveedor_id, numero_convenio, tipo, fecha_inicio, fecha_fin, valor, condiciones, usuario_creacion)
            VALUES (:proveedor_id, :numero_convenio, :tipo, :fecha_inicio, :fecha_fin, :valor, :condiciones, :usuario_creacion)
            """,
            datos,
        )

    @staticmethod
    def cambiar_estado(convenio_id: int, estado: str):
        ejecutar("UPDATE convenios SET estado=? WHERE id=?", (estado, convenio_id))
