"""
=========================================================
HomeCare Enterprise
Repositorio de Nomina
=========================================================
"""

from database.database import consultar, consultar_todos, consultar_uno, ejecutar


class NominaRepository:

    # ------------------------------------------------------
    # TIEMPOS TRABAJADOS (fuente de la nómina)
    # ------------------------------------------------------

    @staticmethod
    def horas_por_profesional(fecha_inicio: str, fecha_fin: str):
        """
        Agrupa, por profesional, las horas realmente
        trabajadas (marcadas con ingreso y salida) dentro
        del periodo, junto con el numero de visitas.
        """

        return consultar_todos(
            """
            SELECT
                pr.profesional_id,
                pf.nombre_completo,
                pf.documento,
                pf.tipo_contrato,
                pf.valor_hora,
                pf.salario_fijo,
                pf.especialidad_principal,
                COUNT(pr.id) AS numero_visitas,
                SUM(COALESCE(pr.horas_trabajadas, 0)) AS horas_trabajadas
            FROM programaciones pr
            JOIN profesionales pf ON pf.id = pr.profesional_id
            WHERE pr.hora_real_inicio IS NOT NULL
              AND pr.hora_real_fin IS NOT NULL
              AND pr.fecha BETWEEN ? AND ?
              AND pr.liquidado = 0
            GROUP BY pr.profesional_id
            ORDER BY pf.nombre_completo
            """,
            (fecha_inicio, fecha_fin),
        )

    @staticmethod
    def visitas_a_liquidar(profesional_id: int, fecha_inicio: str, fecha_fin: str):
        return consultar_todos(
            """
            SELECT * FROM programaciones
            WHERE profesional_id=?
              AND hora_real_inicio IS NOT NULL
              AND hora_real_fin IS NOT NULL
              AND fecha BETWEEN ? AND ?
              AND liquidado = 0
            ORDER BY fecha, hora_real_inicio
            """,
            (profesional_id, fecha_inicio, fecha_fin),
        )

    @staticmethod
    def marcar_visitas_liquidadas(profesional_id: int, fecha_inicio: str, fecha_fin: str, nomina_id: int):
        ejecutar(
            """
            UPDATE programaciones
            SET liquidado = 1, nomina_id = ?
            WHERE profesional_id=?
              AND hora_real_inicio IS NOT NULL
              AND hora_real_fin IS NOT NULL
              AND fecha BETWEEN ? AND ?
              AND liquidado = 0
            """,
            (nomina_id, profesional_id, fecha_inicio, fecha_fin),
        )

    # ------------------------------------------------------
    # NÓMINA (cabecera + detalle)
    # ------------------------------------------------------

    @staticmethod
    def crear_nomina(periodo_inicio: str, periodo_fin: str, usuario_generacion, total_pagar: float) -> int:
        return ejecutar(
            """
            INSERT INTO nomina (periodo_inicio, periodo_fin, usuario_generacion, total_pagar)
            VALUES (?,?,?,?)
            """,
            (periodo_inicio, periodo_fin, usuario_generacion, total_pagar),
        )

    @staticmethod
    def agregar_detalle(nomina_id: int, detalle: dict):
        return ejecutar(
            """
            INSERT INTO nomina_detalle (
                nomina_id, profesional_id, tipo_contrato, numero_visitas,
                horas_trabajadas, valor_hora, salario_fijo, auxilio_transporte, valor_a_pagar
            ) VALUES (
                :nomina_id, :profesional_id, :tipo_contrato, :numero_visitas,
                :horas_trabajadas, :valor_hora, :salario_fijo, :auxilio_transporte, :valor_a_pagar
            )
            """,
            {**detalle, "nomina_id": nomina_id},
        )

    @staticmethod
    def listar_nominas():
        return consultar_todos("SELECT * FROM nomina ORDER BY fecha_generacion DESC")

    @staticmethod
    def obtener_nomina(nomina_id: int):
        return consultar_uno("SELECT * FROM nomina WHERE id=?", (nomina_id,))

    @staticmethod
    def detalle_nomina(nomina_id: int):
        return consultar_todos(
            """
            SELECT nd.*, pf.nombre_completo, pf.documento
            FROM nomina_detalle nd
            JOIN profesionales pf ON pf.id = nd.profesional_id
            WHERE nd.nomina_id=?
            ORDER BY pf.nombre_completo
            """,
            (nomina_id,),
        )

    @staticmethod
    def marcar_pagado(detalle_id: int, fecha_pago: str):
        ejecutar(
            "UPDATE nomina_detalle SET estado_pago='Pagado', fecha_pago=? WHERE id=?",
            (fecha_pago, detalle_id),
        )
