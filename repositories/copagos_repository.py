"""HomeCare Enterprise - Repositorio: Copagos"""

from database.database import consultar_todos, consultar_uno, ejecutar


class CopagosRepository:

    @staticmethod
    def listar_por_paciente(paciente_id: int):
        return consultar_todos(
            "SELECT * FROM copagos WHERE paciente_id=? ORDER BY fecha_creacion DESC",
            (paciente_id,),
        )

    @staticmethod
    def listar_pendientes():
        return consultar_todos(
            """
            SELECT c.*, p.primer_nombre, p.primer_apellido, p.documento
            FROM copagos c
            JOIN pacientes p ON p.id = c.paciente_id
            WHERE c.pagado = 0
            ORDER BY c.fecha_creacion DESC
            """
        )

    @staticmethod
    def obtener(copago_id: int):
        return consultar_uno("SELECT * FROM copagos WHERE id=?", (copago_id,))

    @staticmethod
    def crear(datos: dict) -> int:
        return ejecutar(
            """
            INSERT INTO copagos (
                paciente_id, programacion_id, orden_id, concepto,
                valor_copago, observaciones, usuario_creacion
            ) VALUES (
                :paciente_id, :programacion_id, :orden_id, :concepto,
                :valor_copago, :observaciones, :usuario_creacion
            )
            """,
            datos,
        )

    @staticmethod
    def marcar_pago(copago_id: int, metodo_pago: str, fecha_pago: str):
        ejecutar(
            "UPDATE copagos SET pagado=1, metodo_pago=?, fecha_pago=? WHERE id=?",
            (metodo_pago, fecha_pago, copago_id),
        )

    @staticmethod
    def vincular_factura(copago_id: int, factura_id: int):
        ejecutar(
            "UPDATE copagos SET factura_id=? WHERE id=?",
            (factura_id, copago_id),
        )
