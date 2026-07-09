"""HomeCare Enterprise - Repositorio: Servicios asignados al paciente"""

from database.database import consultar_todos, consultar_uno, ejecutar


class ServiciosPacienteRepository:

    @staticmethod
    def listar_por_paciente(paciente_id: int):
        return consultar_todos(
            """
            SELECT sp.*,
                   COALESCE(pr.nombre_completo, pr_sesion.nombre_completo) AS profesional,
                   COUNT(pv.id) AS total_sesiones_reales,
                   SUM(CASE WHEN pv.estado IN ('Programada', 'Firmada') THEN 1 ELSE 0 END) AS sesiones_programadas,
                   SUM(CASE WHEN pv.estado = 'Pendiente' THEN 1 ELSE 0 END) AS sesiones_pendientes
            FROM servicios_paciente sp
            LEFT JOIN profesionales pr ON pr.id = sp.profesional_id
            LEFT JOIN planilla_visitas pv ON pv.servicio_paciente_id = sp.id
            LEFT JOIN profesionales pr_sesion ON pr_sesion.id = (
                SELECT profesional_id FROM planilla_visitas
                WHERE servicio_paciente_id = sp.id AND profesional_id IS NOT NULL
                ORDER BY id LIMIT 1
            )
            WHERE sp.paciente_id=?
            GROUP BY sp.id
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
