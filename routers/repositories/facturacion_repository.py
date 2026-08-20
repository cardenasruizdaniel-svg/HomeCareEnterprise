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
        datos.setdefault("entidad_responsable_pago", "Particular")
        datos.setdefault("fecha_vencimiento", None)
        return ejecutar(
            """
            INSERT INTO facturas_electronicas (
                prefijo, numero, copago_id, servicio_paciente_id, concepto, paciente_id, valor_subtotal,
                valor_iva, valor_total, forma_pago, medio_pago, cufe,
                estado, entidad_responsable_pago, fecha_vencimiento, xml_path, pdf_path, usuario_creacion
            ) VALUES (
                :prefijo, :numero, :copago_id, :servicio_paciente_id, :concepto, :paciente_id, :valor_subtotal,
                :valor_iva, :valor_total, :forma_pago, :medio_pago, :cufe,
                :estado, :entidad_responsable_pago, :fecha_vencimiento, :xml_path, :pdf_path, :usuario_creacion
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

    @staticmethod
    def marcar_pagada(factura_id: int, valor_pagado: float, metodo_pago: str, fecha_pago: str):
        ejecutar(
            """
            UPDATE facturas_electronicas
            SET estado_cartera='Pagada', valor_pagado=?, metodo_pago_recibido=?, fecha_pago=?
            WHERE id=?
            """,
            (valor_pagado, metodo_pago, fecha_pago, factura_id),
        )

    @staticmethod
    def anular(factura_id: int, motivo: str):
        ejecutar(
            "UPDATE facturas_electronicas SET estado='Anulada', estado_cartera='Anulada', motivo_anulacion=? WHERE id=?",
            (motivo, factura_id),
        )

    @staticmethod
    def marcar_vencidas():
        """Pasa a 'Vencida' toda factura pendiente de pago cuya fecha de vencimiento ya pasó."""
        ejecutar(
            """
            UPDATE facturas_electronicas
            SET estado_cartera='Vencida'
            WHERE estado_cartera='Pendiente de pago'
              AND fecha_vencimiento IS NOT NULL
              AND date(fecha_vencimiento) < date('now')
            """
        )

    @staticmethod
    def listar_cartera(estado_cartera=None):
        condicion = "WHERE f.estado != 'Anulada'"
        parametros = []
        if estado_cartera:
            condicion += " AND f.estado_cartera=?"
            parametros.append(estado_cartera)
        return consultar_todos(
            f"""
            SELECT f.*, p.primer_nombre, p.primer_apellido, p.documento, p.eps,
                   CAST(julianday('now') - julianday(f.fecha_vencimiento) AS INTEGER) AS dias_vencida
            FROM facturas_electronicas f
            JOIN pacientes p ON p.id = f.paciente_id
            {condicion}
            ORDER BY f.fecha_vencimiento
            """,
            tuple(parametros),
        )

    @staticmethod
    def resumen_dashboard():
        return consultar_uno(
            """
            SELECT
                COUNT(*) AS total_facturas,
                SUM(CASE WHEN estado != 'Anulada' THEN valor_total ELSE 0 END) AS total_facturado,
                SUM(CASE WHEN estado_cartera='Pagada' THEN valor_pagado ELSE 0 END) AS total_cobrado,
                SUM(CASE WHEN estado_cartera='Pendiente de pago' THEN valor_total ELSE 0 END) AS cartera_pendiente,
                SUM(CASE WHEN estado_cartera='Vencida' THEN valor_total ELSE 0 END) AS cartera_vencida,
                SUM(CASE WHEN estado_cartera='Pendiente de pago' THEN 1 ELSE 0 END) AS numero_pendientes,
                SUM(CASE WHEN estado_cartera='Vencida' THEN 1 ELSE 0 END) AS numero_vencidas,
                SUM(CASE WHEN estado='Anulada' THEN 1 ELSE 0 END) AS numero_anuladas
            FROM facturas_electronicas
            """
        )

    @staticmethod
    def facturado_por_mes(meses_atras: int = 6):
        return consultar_todos(
            """
            SELECT strftime('%Y-%m', fecha_emision) AS mes,
                   SUM(CASE WHEN estado != 'Anulada' THEN valor_total ELSE 0 END) AS total_facturado,
                   COUNT(*) AS numero_facturas
            FROM facturas_electronicas
            WHERE date(fecha_emision) >= date('now', ?)
            GROUP BY mes
            ORDER BY mes
            """,
            (f"-{meses_atras} months",),
        )

    @staticmethod
    def top_eps():
        return consultar_todos(
            """
            SELECT COALESCE(NULLIF(p.eps,''), 'Particular / Sin EPS') AS eps,
                   SUM(CASE WHEN f.estado != 'Anulada' THEN f.valor_total ELSE 0 END) AS total_facturado,
                   COUNT(*) AS numero_facturas
            FROM facturas_electronicas f
            JOIN pacientes p ON p.id = f.paciente_id
            GROUP BY eps
            ORDER BY total_facturado DESC
            LIMIT 8
            """
        )

    @staticmethod
    def pendientes_facturar():
        """
        Servicios de pacientes con sesiones YA realizadas (con
        ingreso y salida marcados) que todavia no tienen ninguna
        factura generada -- la cola de "esto ya se prestó, hace
        falta facturarlo".
        """
        return consultar_todos(
            """
            SELECT sp.id AS servicio_id, sp.tipo_servicio, sp.subtipo, sp.paciente_id,
                   p.primer_nombre, p.primer_apellido, p.documento, p.eps,
                   COUNT(pv.id) AS sesiones_prestadas,
                   MAX(pg.fecha) AS ultima_sesion
            FROM servicios_paciente sp
            JOIN pacientes p ON p.id = sp.paciente_id
            JOIN planilla_visitas pv ON pv.servicio_paciente_id = sp.id
            JOIN programaciones pg ON pg.id = pv.programacion_id
            WHERE pg.hora_real_inicio IS NOT NULL AND pg.hora_real_fin IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM facturas_electronicas f
                  WHERE f.servicio_paciente_id = sp.id AND f.estado != 'Anulada'
              )
            GROUP BY sp.id
            ORDER BY ultima_sesion DESC
            """
        )
