"""HomeCare Enterprise - Repositorio: Plantillas de texto para visitas"""

from database.database import consultar_todos, consultar_uno, ejecutar


class PlantillasVisitaRepository:

    @staticmethod
    def listar_disponibles_para_profesional(rol_profesional: str, profesional_id: int = None):
        """
        Devuelve las plantillas que le corresponden a ESTE
        profesional segun su rol/perfil: las de uso general
        para su rol (o "Todos"), creadas por administracion,
        MAS las suyas propias (las que el mismo creo para si).
        """
        return consultar_todos(
            """
            SELECT * FROM plantillas_visita
            WHERE activo=1
              AND (
                    (creado_por_administracion=1 AND (rol_destinatario=? OR rol_destinatario='Todos'))
                    OR profesional_id=?
                  )
            ORDER BY creado_por_administracion DESC, nombre
            """,
            (rol_profesional, profesional_id),
        )

    @staticmethod
    def listar_todas():
        return consultar_todos(
            """
            SELECT pv.*, pr.nombre_completo AS profesional
            FROM plantillas_visita pv
            LEFT JOIN profesionales pr ON pr.id = pv.profesional_id
            WHERE pv.activo=1
            ORDER BY pv.rol_destinatario, pv.nombre
            """
        )

    @staticmethod
    def obtener(plantilla_id: int):
        return consultar_uno("SELECT * FROM plantillas_visita WHERE id=?", (plantilla_id,))

    @staticmethod
    def crear(datos: dict) -> int:
        return ejecutar(
            """
            INSERT INTO plantillas_visita(
                nombre, tipo_servicio, subtipo, rol_destinatario, contenido, profesional_id,
                creado_por_administracion, usuario_creacion
            ) VALUES (
                :nombre, :tipo_servicio, :subtipo, :rol_destinatario, :contenido, :profesional_id,
                :creado_por_administracion, :usuario_creacion
            )
            """,
            datos,
        )

    @staticmethod
    def desactivar(plantilla_id: int):
        ejecutar("UPDATE plantillas_visita SET activo=0 WHERE id=?", (plantilla_id,))
