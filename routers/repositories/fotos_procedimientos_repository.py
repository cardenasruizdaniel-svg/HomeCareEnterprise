"""HomeCare Enterprise - Repositorio: Fotos de Procedimientos"""

from database.database import consultar_todos, consultar_uno, ejecutar


class FotosProcedimientosRepository:

    @staticmethod
    def listar_por_paciente(paciente_id: int):
        return consultar_todos(
            """
            SELECT fp.*, pr.nombre_completo AS profesional
            FROM fotos_procedimientos fp
            LEFT JOIN profesionales pr ON pr.id = fp.profesional_id
            WHERE fp.paciente_id=?
            ORDER BY fp.fecha DESC
            """,
            (paciente_id,),
        )

    @staticmethod
    def obtener(foto_id: int):
        return consultar_uno("SELECT * FROM fotos_procedimientos WHERE id=?", (foto_id,))

    @staticmethod
    def crear(datos: dict) -> int:
        return ejecutar(
            """
            INSERT INTO fotos_procedimientos(
                paciente_id, descripcion, foto_base64, profesional_id, usuario_creacion
            ) VALUES (
                :paciente_id, :descripcion, :foto_base64, :profesional_id, :usuario_creacion
            )
            """,
            datos,
        )

    @staticmethod
    def eliminar(foto_id: int):
        ejecutar("DELETE FROM fotos_procedimientos WHERE id=?", (foto_id,))
