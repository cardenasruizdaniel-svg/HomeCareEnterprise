"""
=========================================================
HomeCare Enterprise
Repositorio: Contratos
=========================================================
"""

from database.database import consultar_todos, consultar_uno, ejecutar


class ContratosRepository:

    @staticmethod
    def listar():
        return consultar_todos(
            """
            SELECT c.*, pf.nombre_completo, pf.documento, ca.nombre AS nombre_cargo
            FROM contratos c
            JOIN profesionales pf ON pf.id = c.profesional_id
            JOIN cargos ca ON ca.id = c.cargo_id
            ORDER BY c.fecha_inicio DESC
            """
        )

    @staticmethod
    def listar_por_profesional(profesional_id: int):
        return consultar_todos(
            """
            SELECT c.*, ca.nombre AS nombre_cargo
            FROM contratos c
            JOIN cargos ca ON ca.id = c.cargo_id
            WHERE c.profesional_id=?
            ORDER BY c.fecha_inicio DESC
            """,
            (profesional_id,),
        )

    @staticmethod
    def obtener(contrato_id: int):
        return consultar_uno(
            """
            SELECT c.*, pf.nombre_completo, pf.documento, ca.nombre AS nombre_cargo
            FROM contratos c
            JOIN profesionales pf ON pf.id = c.profesional_id
            JOIN cargos ca ON ca.id = c.cargo_id
            WHERE c.id=?
            """,
            (contrato_id,),
        )

    @staticmethod
    def contrato_activo(profesional_id: int):
        return consultar_uno(
            """
            SELECT c.*, ca.nombre AS nombre_cargo
            FROM contratos c
            JOIN cargos ca ON ca.id = c.cargo_id
            WHERE c.profesional_id=? AND c.estado='Activo'
            ORDER BY c.fecha_inicio DESC
            LIMIT 1
            """,
            (profesional_id,),
        )

    @staticmethod
    def crear(datos: dict) -> int:
        return ejecutar(
            """
            INSERT INTO contratos (
                profesional_id, cargo_id, tipo_contrato, modalidad_pago,
                salario_mensual, valor_hora, periodicidad_pago, fecha_inicio,
                fecha_fin, nivel_riesgo_arl, eps, fondo_pension, fondo_cesantias,
                caja_compensacion, observaciones, usuario_creacion
            ) VALUES (
                :profesional_id, :cargo_id, :tipo_contrato, :modalidad_pago,
                :salario_mensual, :valor_hora, :periodicidad_pago, :fecha_inicio,
                :fecha_fin, :nivel_riesgo_arl, :eps, :fondo_pension, :fondo_cesantias,
                :caja_compensacion, :observaciones, :usuario_creacion
            )
            """,
            datos,
        )

    @staticmethod
    def finalizar(contrato_id: int, fecha_fin: str):
        ejecutar(
            "UPDATE contratos SET estado='Finalizado', fecha_fin=? WHERE id=?",
            (fecha_fin, contrato_id),
        )
