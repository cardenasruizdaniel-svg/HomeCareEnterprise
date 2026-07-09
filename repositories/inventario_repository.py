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
            INSERT INTO insumos(nombre, categoria, unidad_medida, stock_minimo)
            VALUES (:nombre, :categoria, :unidad_medida, :stock_minimo)
            """,
            datos,
        )

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
                paciente_id, profesional_id, motivo, usuario_creacion
            ) VALUES (
                :insumo_id, :tipo, :cantidad, :proveedor_id, :numero_factura, :costo_unitario,
                :paciente_id, :profesional_id, :motivo, :usuario_creacion
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
