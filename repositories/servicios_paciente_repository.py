"""HomeCare Enterprise - Repositorio: Servicios asignados al paciente"""

from database.database import consultar_todos, consultar_uno, ejecutar


class ServiciosPacienteRepository:

    @staticmethod
    def listar_por_paciente(paciente_id: int):
        return consultar_todos(
            """
            SELECT sp.*, pr.nombre_completo AS profesional
            FROM servicios_paciente sp
            LEFT JOIN profesionales pr ON pr.id = sp.profesional_id
            WHERE sp.paciente_id=?
            ORDER BY sp.fecha_inicio DESC
            """,
            (paciente_id,),
        )

    @staticmethod
    def obtener(servicio_id: int):
        return consultar_uno("SELECT * FROM servicios_paciente WHERE id=?", (servicio_id,))

    @staticmethod
    def crear(datos: dict) -> int:
        return ejecutar(
            """
            INSERT INTO servicios_paciente(
                paciente_id, tipo_servicio, subtipo, profesional_id, frecuencia,
                fecha_inicio, fecha_fin, hora_inicio, hora_fin, indicaciones, usuario_creacion
            ) VALUES (
                :paciente_id, :tipo_servicio, :subtipo, :profesional_id, :frecuencia,
                :fecha_inicio, :fecha_fin, :hora_inicio, :hora_fin, :indicaciones, :usuario_creacion
            )
            """,
            datos,
        )

    @staticmethod
    def cambiar_estado(servicio_id: int, estado: str):
        ejecutar("UPDATE servicios_paciente SET estado=? WHERE id=?", (estado, servicio_id))

    @staticmethod
    def listar_activos_por_profesional(profesional_id: int):
        return consultar_todos(
            """
            SELECT sp.*, (pa.primer_nombre || ' ' || pa.primer_apellido) AS paciente
            FROM servicios_paciente sp
            JOIN pacientes pa ON pa.id = sp.paciente_id
            WHERE sp.profesional_id=? AND sp.estado='Activo'
            ORDER BY sp.fecha_inicio
            """,
            (profesional_id,),
        )
