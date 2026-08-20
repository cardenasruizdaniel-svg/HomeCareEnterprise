"""HomeCare Enterprise - Repositorio: Planilla de visitas"""

from database.database import consultar_todos, consultar_uno, ejecutar


class PlanillaVisitasRepository:

    @staticmethod
    def listar_por_servicio(servicio_paciente_id: int):
        return consultar_todos(
            "SELECT * FROM planilla_visitas WHERE servicio_paciente_id=? ORDER BY fecha",
            (servicio_paciente_id,),
        )

    @staticmethod
    def obtener(planilla_id: int):
        return consultar_uno("SELECT * FROM planilla_visitas WHERE id=?", (planilla_id,))

    @staticmethod
    def obtener_por_programacion(programacion_id: int):
        return consultar_uno("SELECT * FROM planilla_visitas WHERE programacion_id=?", (programacion_id,))

    @staticmethod
    def firmar(planilla_id: int, datos: dict):
        ejecutar(
            """
            UPDATE planilla_visitas
            SET nombre_acompanante=:nombre_acompanante,
                firmante=:firmante,
                firma_base64=:firma_base64,
                foto_base64=:foto_base64,
                firma_fecha_hora=:firma_fecha_hora,
                firma_latitud=:firma_latitud,
                firma_longitud=:firma_longitud,
                estado='Firmada'
            WHERE id=:planilla_id
            """,
            {**datos, "planilla_id": planilla_id},
        )
