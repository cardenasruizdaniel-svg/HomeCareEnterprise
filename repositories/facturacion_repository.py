"""HomeCare Enterprise - Repositorio: Facturacion electronica"""

from database.database import consultar_escalar, consultar_todos, consultar_uno, ejecutar


class FacturacionRepository:

    @staticmethod
    def siguiente_numero(prefijo: str) -> int:
        maximo = consultar_escalar(
            "SELECT MAX(numero) FROM facturas_electronicas WHERE prefijo=?",
            (prefijo,),
        )
        return (maximo or 0) + 1

    @staticmethod
    def crear(datos: dict) -> int:
        datos.setdefault("servicio_paciente_id", None)
        datos.setdefault("concepto", "")
        return ejecutar(
            """
            INSERT INTO facturas_electronicas (
                prefijo, numero, copago_id, servicio_paciente_id, concepto, paciente_id, valor_subtotal,
                valor_iva, valor_total, forma_pago, medio_pago, cufe,
                estado, xml_path, pdf_path, usuario_creacion
            ) VALUES (
                :prefijo, :numero, :copago_id, :servicio_paciente_id, :concepto, :paciente_id, :valor_subtotal,
                :valor_iva, :valor_total, :forma_pago, :medio_pago, :cufe,
                :estado, :xml_path, :pdf_path, :usuario_creacion
            )
            """,
            datos,
        )

    @staticmethod
    def reporte_por_paciente(fecha_desde=None, fecha_hasta=None):
        condicion = ""
        parametros = []
        if fecha_desde and fecha_hasta:
            condicion = "WHERE date(f.fecha_emision) BETWEEN ? AND ?"
            parametros = [fecha_desde, fecha_hasta]
        return consultar_todos(
            f"""
            SELECT p.id AS paciente_id, p.primer_nombre, p.primer_apellido, p.documento, p.eps,
                   COUNT(f.id) AS total_facturas, SUM(f.valor_total) AS valor_total
            FROM facturas_electronicas f
            JOIN pacientes p ON p.id = f.paciente_id
            {condicion}
            GROUP BY p.id
            ORDER BY valor_total DESC
            """,
            tuple(parametros),
        )

    @staticmethod
    def reporte_por_eps(fecha_desde=None, fecha_hasta=None):
        condicion = ""
        parametros = []
        if fecha_desde and fecha_hasta:
            condicion = "WHERE date(f.fecha_emision) BETWEEN ? AND ?"
            parametros = [fecha_desde, fecha_hasta]
        return consultar_todos(
            f"""
            SELECT COALESCE(NULLIF(p.eps, ''), 'Sin EPS / Particular') AS eps,
                   COUNT(f.id) AS total_facturas, SUM(f.valor_total) AS valor_total
            FROM facturas_electronicas f
            JOIN pacientes p ON p.id = f.paciente_id
            {condicion}
            GROUP BY eps
            ORDER BY valor_total DESC
            """,
            tuple(parametros),
        )

    @staticmethod
    def reporte_por_fecha(fecha_desde: str, fecha_hasta: str):
        return consultar_todos(
            """
            SELECT date(f.fecha_emision) AS fecha, COUNT(f.id) AS total_facturas, SUM(f.valor_total) AS valor_total
            FROM facturas_electronicas f
            WHERE date(f.fecha_emision) BETWEEN ? AND ?
            GROUP BY date(f.fecha_emision)
            ORDER BY fecha
            """,
            (fecha_desde, fecha_hasta),
        )

    @staticmethod
    def listar_por_paciente(paciente_id: int):
        return consultar_todos(
            "SELECT * FROM facturas_electronicas WHERE paciente_id=? ORDER BY fecha_emision DESC",
            (paciente_id,),
        )

    @staticmethod
    def listar_todas():
        return consultar_todos(
            """
            SELECT f.*, p.primer_nombre, p.primer_apellido, p.documento
            FROM facturas_electronicas f
            JOIN pacientes p ON p.id = f.paciente_id
            ORDER BY f.fecha_emision DESC
            """
        )

    @staticmethod
    def obtener(factura_id: int):
        return consultar_uno("SELECT * FROM facturas_electronicas WHERE id=?", (factura_id,))

    @staticmethod
    def actualizar_pdf_path(factura_id: int, pdf_path: str):
        ejecutar(
            "UPDATE facturas_electronicas SET pdf_path=? WHERE id=?",
            (pdf_path, factura_id),
        )
