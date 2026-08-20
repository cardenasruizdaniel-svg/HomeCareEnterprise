"""HomeCare Enterprise - Repositorio: Plantillas de texto para visitas"""

from database.database import consultar_todos, consultar_uno, ejecutar


class PlantillasVisitaRepository:

    @staticmethod
    def listar_candidatas(profesional_id: int = None):
        """
        Trae todas las plantillas activas que PODRÍAN
        corresponderle a este profesional: las creadas por
        administración (el servicio filtra después cuáles le
        aplican, según los roles asignados a cada una -- que
        pueden ser varios a la vez), MAS las suyas propias
        (las que el mismo creó para sí).
        """
        return consultar_todos(
            """
            SELECT * FROM plantillas_visita
            WHERE activo=1
              AND (creado_por_administracion=1 OR profesional_id=?)
            ORDER BY creado_por_administracion DESC, nombre
            """,
            (profesional_id,),
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

    @staticmethod
    def actualizar(plantilla_id: int, datos: dict):
        datos = {**datos, "id": plantilla_id}
        ejecutar(
            """
            UPDATE plantillas_visita
            SET nombre=:nombre, tipo_servicio=:tipo_servicio, subtipo=:subtipo,
                rol_destinatario=:rol_destinatario, contenido=:contenido
            WHERE id=:id
            """,
            datos,
        )
