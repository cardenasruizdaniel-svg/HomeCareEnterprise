"""
==============================================================
HomeCare Enterprise
Repositorio de Programaciones
Sprint 3.4A
==============================================================
"""

from __future__ import annotations

from typing import Any

from database.database import get_connection

from repositories.base_repository import BaseRepository

from repositories.query_builder import QueryBuilder

from repositories.pagination import Pagination

from repositories.filters import Filters

from repositories.audit import Audit

from repositories.exceptions import (
    EntityNotFoundError,
    ValidationError,
    QueryError,
)


class ProgramacionRepository(BaseRepository):

    TABLE = "programaciones"

    PRIMARY_KEY = "id"

    ENTITY_NAME = "Programación"

    """
    Repositorio principal de Programaciones.

    Centraliza las operaciones CRUD,
    Agenda Clínica,
    Motor Inteligente,
    Centro de Despacho
    y Dashboard Ejecutivo.
    """

    def __init__(self):
        super().__init__()

    # =====================================================
    # INFRAESTRUCTURA
    # =====================================================

    @classmethod
    def table(cls):
        return cls.TABLE

    @classmethod
    def entity(cls):
        return cls.ENTITY_NAME

    def _not_found(self, programacion_id: int):
        raise EntityNotFoundError(
            f"Programación {programacion_id} no encontrada."
        )

    def query(self) -> QueryBuilder:
        return QueryBuilder(self.TABLE)

    def audit_insert(self, registro_id: int, datos=None):
        Audit.insert(
            self.TABLE,
            registro_id,
            datos=datos,
        )

    def audit_update(self, registro_id: int, datos=None):
        Audit.update(
            self.TABLE,
            registro_id,
            datos=datos,
        )

    def audit_delete(self, registro_id: int):
        Audit.delete(
            self.TABLE,
            registro_id,
        )

    # ======================================================
    # CONSULTAS GENERALES
    # ======================================================

    def listar(self):

        sql = """
            SELECT *
            FROM programaciones
            WHERE eliminado = 0
            ORDER BY fecha, hora_inicio
        """

        return self.fetch_all(sql)

    # ======================================================

    def obtener(self, programacion_id: int):

        sql = """
            SELECT *
            FROM programaciones
            WHERE id = ?
              AND eliminado = 0
        """

        dato = self.fetch_one(
            sql,
            (programacion_id,),
        )

        if dato is None:
            self._not_found(programacion_id)

        return dato    

    # ======================================================

    def obtener_uuid(self, uuid: str):

        sql = """
            SELECT *
            FROM programaciones
            WHERE uuid = ?
              AND eliminado = 0
        """

        return self.fetch_one(
            sql,
            (uuid,),
        )

    # ======================================================

    def existe(self, programacion_id: int):

        return super().exists(
            self.TABLE,
            programacion_id,
        )

    # ======================================================
    # CREAR
    # ======================================================
    
    def crear(
        self,
        datos: dict[str, Any],
    ) -> int:
        """
        Crea una nueva programación.
        """

        sql = """
            INSERT INTO programaciones(

                uuid,
                paciente_id,
                profesional_id,
                servicio,
                procedimiento,
                codigo_cups,
                valor_servicio,
                diagnostico_id,
                prioridad,
                estado,
                fecha,
                hora_inicio,
                hora_fin,
                duracion,
                direccion,
                barrio,
                municipio,
                departamento,
                latitud,
                longitud,
                telefono_contacto,
                nombre_contacto,
                observaciones,
                usuario_creacion

            )

            VALUES(

                :uuid,
                :paciente_id,
                :profesional_id,
                :servicio,
                :procedimiento,
                :codigo_cups,
                :valor_servicio,
                :diagnostico_id,
                :prioridad,
                :estado,
                :fecha,
                :hora_inicio,
                :hora_fin,
                :duracion,
                :direccion,
                :barrio,
                :municipio,
                :departamento,
                :latitud,
                :longitud,
                :telefono_contacto,
                :nombre_contacto,
                :observaciones,
                :usuario_creacion

            )
        """

        nuevo_id = self.execute(sql, datos)

        self.audit_insert(
            nuevo_id,
            datos,
        )

        return nuevo_id

    # ======================================================
    # ELIMINAR
    # ======================================================

    @staticmethod
    def eliminar(

        programacion_id: int,

    ):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            DELETE

            FROM programaciones

            WHERE id=?

        """,

        (

            programacion_id,

        ))

        conexion.commit()

        conexion.close()

            # ======================================================
    # AGENDA DEL DÍA
    # ======================================================

    @staticmethod
    def agenda_dia(fecha: str):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT

                p.*,

                (pa.primer_nombre || ' ' || pa.primer_apellido) AS paciente,

                pr.nombre_completo AS profesional

            FROM programaciones p

            LEFT JOIN pacientes pa

                ON pa.id = p.paciente_id

            LEFT JOIN profesionales pr

                ON pr.id = p.profesional_id

            WHERE p.fecha=?

            ORDER BY

                p.hora_inicio

        """,(fecha,))

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # AGENDA POR RANGO DE FECHAS (semana / mes / calendario)
    # ======================================================

    @staticmethod
    def agenda_rango(fecha_inicio: str, fecha_fin: str):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT

                p.*,

                (pa.primer_nombre || ' ' || pa.primer_apellido) AS paciente,

                pr.nombre_completo AS profesional

            FROM programaciones p

            LEFT JOIN pacientes pa

                ON pa.id = p.paciente_id

            LEFT JOIN profesionales pr

                ON pr.id = p.profesional_id

            WHERE p.fecha BETWEEN ? AND ?

              AND p.eliminado = 0

            ORDER BY

                p.fecha, p.hora_inicio

        """, (fecha_inicio, fecha_fin))

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # AGENDA POR PROFESIONAL
    # ======================================================

    @staticmethod
    def agenda_profesional(

        profesional_id: int,

        fecha: str,

        incluir_canceladas: bool = False,

    ):

        conexion = get_connection()

        cursor = conexion.cursor()

        condicion_estado = "" if incluir_canceladas else "AND estado != 'Cancelada'"

        cursor.execute(f"""

            SELECT *

            FROM programaciones

            WHERE profesional_id=?

            AND fecha=?

            {condicion_estado}

            ORDER BY hora_inicio

        """,

        (

            profesional_id,

            fecha,

        ))

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # AGENDA PACIENTE
    # ======================================================

    @staticmethod
    def agenda_paciente(

        paciente_id: int,

    ):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT *

            FROM programaciones

            WHERE paciente_id=?

            ORDER BY

                fecha DESC,

                hora_inicio DESC

        """,

        (

            paciente_id,

        ))

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # AGENDA ENTRE FECHAS (ver agenda_rango arriba, con JOINs
    # a pacientes/profesionales -- este metodo duplicado sin
    # JOINs se elimino para no volver a shadowearlo)

    # ======================================================
    # PROGRAMACIONES POR ESTADO
    # ======================================================

    @staticmethod
    def por_estado(

        estado: str,

    ):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT *

            FROM programaciones

            WHERE estado=?

            ORDER BY

                fecha,

                hora_inicio

        """,

        (

            estado,

        ))

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # ACTUALIZAR
    # ======================================================

    @staticmethod
    def actualizar(

        programacion_id: int,

        datos: dict,

    ):

        conexion = get_connection()

        cursor = conexion.cursor()

        datos["id"] = programacion_id

        cursor.execute("""

            UPDATE programaciones

            SET

                profesional_id=:profesional_id,

                servicio=:servicio,

                procedimiento=:procedimiento,

                prioridad=:prioridad,

                fecha=:fecha,

                hora_inicio=:hora_inicio,

                hora_fin=:hora_fin,

                duracion=:duracion,

                direccion=:direccion,

                barrio=:barrio,

                municipio=:municipio,

                departamento=:departamento,

                latitud=:latitud,

                longitud=:longitud,

                observaciones=:observaciones,

                usuario_actualizacion=:usuario_actualizacion,

                fecha_actualizacion=CURRENT_TIMESTAMP

            WHERE id=:id

        """, datos)

        conexion.commit()

        conexion.close()


    # ======================================================
    # MARCACIÓN REAL DE INGRESO / SALIDA (para nómina)
    # ======================================================

    @staticmethod
    def registrar_ingreso(
        programacion_id: int,
        hora_real_inicio: str,
        latitud=None,
        longitud=None,
        geocerca_ok=None,
        distancia_metros=None,
        foto_base64=None,
    ):

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            UPDATE programaciones

            SET
                hora_real_inicio=?,
                latitud_inicio=?,
                longitud_inicio=?,
                geocerca_inicio_ok=?,
                distancia_inicio_metros=?,
                foto_ingreso_base64=?,
                estado='En Curso',
                fecha_actualizacion=CURRENT_TIMESTAMP

            WHERE id=?

        """, (hora_real_inicio, latitud, longitud, geocerca_ok, distancia_metros, foto_base64, programacion_id))

        conexion.commit()
        conexion.close()

    @staticmethod
    def registrar_salida(
        programacion_id: int,
        hora_real_fin: str,
        horas_trabajadas,
        latitud=None,
        longitud=None,
        geocerca_ok=None,
        distancia_metros=None,
        foto_base64=None,
    ):

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            UPDATE programaciones

            SET
                hora_real_fin=?,
                latitud_fin=?,
                longitud_fin=?,
                horas_trabajadas=?,
                geocerca_fin_ok=?,
                distancia_fin_metros=?,
                foto_salida_base64=?,
                estado='Completada',
                fecha_actualizacion=CURRENT_TIMESTAMP

            WHERE id=?

        """, (hora_real_fin, latitud, longitud, horas_trabajadas, geocerca_ok, distancia_metros, foto_base64, programacion_id))

        conexion.commit()
        conexion.close()


    # ======================================================
    # CAMBIAR ESTADO
    # ======================================================

    @staticmethod
    def cambiar_estado(

        programacion_id: int,

        estado: str,

    ):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            UPDATE programaciones

            SET

                estado=?,

                fecha_actualizacion=CURRENT_TIMESTAMP

            WHERE id=?

        """,

        (

            estado,

            programacion_id,

        ))

        conexion.commit()

        conexion.close()

            # ======================================================
    # VISITAS SIN PROFESIONAL
    # ======================================================

    @staticmethod
    def visitas_sin_profesional():

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT

                p.*,

                (pa.primer_nombre || ' ' || pa.primer_apellido) AS paciente

            FROM programaciones p

            INNER JOIN pacientes pa

                ON pa.id = p.paciente_id

            WHERE

                p.profesional_id IS NULL

                AND p.estado='PROGRAMADA'

            ORDER BY

                p.prioridad DESC,

                p.fecha,

                p.hora_inicio

        """)

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # PROGRAMACIONES PENDIENTES
    # ======================================================

    @staticmethod
    def programaciones_pendientes():

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT *

            FROM programaciones

            WHERE estado='PROGRAMADA'

            ORDER BY

                prioridad DESC,

                fecha,

                hora_inicio

        """)

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # ACTUALIZAR PROFESIONAL
    # ======================================================

    @staticmethod
    def actualizar_profesional(

        programacion_id: int,

        profesional_id: int,

    ):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            UPDATE programaciones

            SET

                profesional_id=?,

                fecha_actualizacion=CURRENT_TIMESTAMP

            WHERE id=?

        """,

        (

            profesional_id,

            programacion_id,

        ))

        conexion.commit()

        conexion.close()


    # ======================================================
    # ACTUALIZAR PRIORIDAD
    # ======================================================

    @staticmethod
    def actualizar_prioridad(

        programacion_id: int,

        prioridad: str,

    ):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            UPDATE programaciones

            SET

                prioridad=?,

                fecha_actualizacion=CURRENT_TIMESTAMP

            WHERE id=?

        """,

        (

            prioridad,

            programacion_id,

        ))

        conexion.commit()

        conexion.close()


    # ======================================================
    # REASIGNAR PROFESIONAL
    # ======================================================

    @staticmethod
    def reasignar_profesional(

        programacion_id: int,

        nuevo_profesional: int,

    ):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            UPDATE programaciones

            SET

                profesional_id=?,

                estado='REASIGNADA',

                fecha_actualizacion=CURRENT_TIMESTAMP

            WHERE id=?

        """,

        (

            nuevo_profesional,

            programacion_id,

        ))

        conexion.commit()

        conexion.close()


    # ======================================================
    # MARCAR DESPACHADA
    # ======================================================

    @staticmethod
    def marcar_despachada(

        programacion_id: int,

    ):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            UPDATE programaciones

            SET

                estado='DESPACHADA',

                fecha_actualizacion=CURRENT_TIMESTAMP

            WHERE id=?

        """,

        (

            programacion_id,

        ))

        conexion.commit()

        conexion.close()


    # ======================================================
    # VALIDAR DISPONIBILIDAD
    # ======================================================

    @staticmethod
    def profesional_disponible(

        profesional_id: int,

        fecha: str,

        hora_inicio: str,

        hora_fin: str,

    ) -> bool:

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT COUNT(*)

            FROM programaciones

            WHERE profesional_id=?

              AND fecha=?

              AND estado NOT IN ('CANCELADA')

              AND (

                    hora_inicio < ?

                AND hora_fin > ?

              )

        """,

        (

            profesional_id,

            fecha,

            hora_fin,

            hora_inicio,

        ))

        ocupado = cursor.fetchone()[0]

        conexion.close()

        return ocupado == 0
    
        # ======================================================
    # VISITAS PROGRAMADAS HOY
    # ======================================================

    @staticmethod
    def programadas_hoy(fecha: str):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT

                p.*,

                (pa.primer_nombre || ' ' || pa.primer_apellido) AS paciente,

                pr.nombre_completo AS profesional

            FROM programaciones p

            LEFT JOIN pacientes pa
                ON pa.id = p.paciente_id

            LEFT JOIN profesionales pr
                ON pr.id = p.profesional_id

            WHERE p.fecha = ?
              AND p.estado = 'PROGRAMADA'

            ORDER BY

                p.prioridad DESC,

                p.hora_inicio

        """, (fecha,))

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # VISITAS EN RUTA
    # ======================================================

    @staticmethod
    def en_ruta(fecha: str):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT *

            FROM programaciones

            WHERE fecha = ?

              AND estado = 'EN_RUTA'

            ORDER BY hora_inicio

        """, (fecha,))

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # VISITAS EN ATENCIÓN
    # ======================================================

    @staticmethod
    def en_atencion(fecha: str):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT *

            FROM programaciones

            WHERE fecha = ?

              AND estado = 'EN_ATENCION'

            ORDER BY hora_inicio

        """, (fecha,))

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # VISITAS FINALIZADAS
    # ======================================================

    @staticmethod
    def finalizadas(fecha: str):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT *

            FROM programaciones

            WHERE fecha = ?

              AND estado = 'FINALIZADA'

            ORDER BY hora_inicio

        """, (fecha,))

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # VISITAS CANCELADAS
    # ======================================================

    @staticmethod
    def canceladas(fecha: str):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT *

            FROM programaciones

            WHERE fecha = ?

              AND estado = 'CANCELADA'

            ORDER BY hora_inicio

        """, (fecha,))

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # CAMBIAR ESTADO OPERATIVO
    # ======================================================

    @staticmethod
    def actualizar_estado_operativo(

        programacion_id: int,

        estado: str,

    ):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            UPDATE programaciones

            SET

                estado=?,

                fecha_actualizacion=CURRENT_TIMESTAMP

            WHERE id=?

        """,

        (

            estado,

            programacion_id,

        ))

        conexion.commit()

        conexion.close()


    # ======================================================
    # DESPACHO DEL PROFESIONAL
    # ======================================================

    @staticmethod
    def despacho_profesional(

        profesional_id: int,

        fecha: str,

    ):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT *

            FROM programaciones

            WHERE profesional_id=?

              AND fecha=?

            ORDER BY

                orden_ruta,

                hora_inicio

        """,

        (

            profesional_id,

            fecha,

        ))

        datos = cursor.fetchall()

        conexion.close()

        return datos
    
        # ======================================================
    # TOTAL DE PROGRAMACIONES
    # ======================================================

    @staticmethod
    def total_programaciones():

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            SELECT COUNT(*)

            FROM programaciones

        """)

        total = cursor.fetchone()[0]

        conexion.close()

        return total


    # ======================================================
    # TOTAL POR ESTADO
    # ======================================================

    @staticmethod
    def total_por_estado():

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            SELECT

                estado,

                COUNT(*) AS total

            FROM programaciones

            GROUP BY estado

            ORDER BY estado

        """)

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # TOTAL POR PROFESIONAL
    # ======================================================

    @staticmethod
    def total_por_profesional():

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            SELECT

                pr.id,

                pr.nombre_completo,

                COUNT(p.id) AS total

            FROM profesionales pr

            LEFT JOIN programaciones p

                ON p.profesional_id = pr.id

            GROUP BY

                pr.id,

                pr.nombre_completo

            ORDER BY total DESC

        """)

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # TOTAL POR MUNICIPIO
    # ======================================================

    @staticmethod
    def total_por_municipio():

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            SELECT

                municipio,

                COUNT(*) AS total

            FROM programaciones

            GROUP BY municipio

            ORDER BY total DESC

        """)

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # TOTAL POR PRIORIDAD
    # ======================================================

    @staticmethod
    def total_por_prioridad():

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            SELECT

                prioridad,

                COUNT(*) AS total

            FROM programaciones

            GROUP BY prioridad

            ORDER BY total DESC

        """)

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # INDICADORES DEL DÍA
    # ======================================================

    @staticmethod
    def indicadores_diarios(fecha: str):

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            SELECT

                COUNT(*) AS total,

                SUM(CASE WHEN estado='PROGRAMADA' THEN 1 ELSE 0 END) AS programadas,

                SUM(CASE WHEN estado='DESPACHADA' THEN 1 ELSE 0 END) AS despachadas,

                SUM(CASE WHEN estado='EN_RUTA' THEN 1 ELSE 0 END) AS en_ruta,

                SUM(CASE WHEN estado='EN_ATENCION' THEN 1 ELSE 0 END) AS en_atencion,

                SUM(CASE WHEN estado='FINALIZADA' THEN 1 ELSE 0 END) AS finalizadas,

                SUM(CASE WHEN estado='CANCELADA' THEN 1 ELSE 0 END) AS canceladas

            FROM programaciones

            WHERE fecha = ?

        """, (fecha,))

        datos = cursor.fetchone()

        conexion.close()

        return datos


    # ======================================================
    # ÚLTIMAS PROGRAMACIONES
    # ======================================================

    @staticmethod
    def ultimas_programaciones(limite: int = 10):

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""

            SELECT *

            FROM programaciones

            ORDER BY

                fecha_creacion DESC

            LIMIT ?

        """, (limite,))

        datos = cursor.fetchall()

        conexion.close()

        return datos
    
        # ======================================================
    # CARGA DE TRABAJO POR PROFESIONAL
    # ======================================================

    @staticmethod
    def carga_profesional(

        profesional_id: int,

        fecha: str,

    ):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT

                COUNT(*) AS visitas,

                COALESCE(

                    SUM(duracion),

                    0

                ) AS minutos

            FROM programaciones

            WHERE profesional_id=?

              AND fecha=?

              AND estado<>'CANCELADA'

        """,

        (

            profesional_id,

            fecha,

        ))

        datos = cursor.fetchone()

        conexion.close()

        return datos


    # ======================================================
    # HORAS PROGRAMADAS
    # ======================================================

    @staticmethod
    def horas_programadas(

        profesional_id: int,

        fecha: str,

    ):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT

                COALESCE(

                    SUM(duracion),

                    0

                )

            FROM programaciones

            WHERE profesional_id=?

              AND fecha=?

              AND estado<>'CANCELADA'

        """,

        (

            profesional_id,

            fecha,

        ))

        minutos = cursor.fetchone()[0]

        conexion.close()

        return round(minutos / 60, 2)


    # ======================================================
    # PROFESIONALES SOBRECARGADOS
    # ======================================================

    @staticmethod
    def profesionales_sobrecargados(

        fecha: str,

        capacidad: int = 8,

    ):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT

                profesional_id,

                SUM(duracion) AS minutos

            FROM programaciones

            WHERE fecha=?

            GROUP BY profesional_id

            HAVING minutos > ?

        """,

        (

            fecha,

            capacidad * 60,

        ))

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # PROFESIONALES LIBRES
    # ======================================================

    @staticmethod
    def profesionales_libres(

        fecha: str,

    ):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT *

            FROM profesionales

            WHERE id NOT IN(

                SELECT DISTINCT profesional_id

                FROM programaciones

                WHERE fecha=?

            )

            AND disponible=1

            ORDER BY nombre_completo

        """,

        (

            fecha,

        ))

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # VISITAS SIN ASIGNAR
    # ======================================================

    @staticmethod
    def visitas_sin_asignar(

        fecha: str,

    ):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT *

            FROM programaciones

            WHERE fecha=?

              AND profesional_id IS NULL

            ORDER BY

                prioridad DESC,

                hora_inicio

        """,

        (

            fecha,

        ))

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # DISTRIBUCIÓN POR SERVICIO
    # ======================================================

    @staticmethod
    def distribucion_servicios(

        fecha: str,

    ):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT

                servicio,

                COUNT(*) total

            FROM programaciones

            WHERE fecha=?

            GROUP BY servicio

            ORDER BY total DESC

        """,

        (

            fecha,

        ))

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # EFICIENCIA OPERATIVA
    # ======================================================

    @staticmethod
    def eficiencia_operativa(

        fecha: str,

    ):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT

                COUNT(*) total,

                SUM(

                    CASE

                        WHEN estado='FINALIZADA'

                        THEN 1

                        ELSE 0

                    END

                ) realizadas

            FROM programaciones

            WHERE fecha=?

        """,

        (

            fecha,

        ))

        datos = cursor.fetchone()

        conexion.close()

        return datos
    
        # ======================================================
    # EXPORTACIÓN PARA REPORTES
    # ======================================================

    @staticmethod
    def exportar_programaciones(

        fecha_inicio: str,

        fecha_fin: str,

    ):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT

                p.*,

                (pa.primer_nombre || ' ' || pa.primer_apellido) AS paciente,

                pr.nombre_completo AS profesional

            FROM programaciones p

            LEFT JOIN pacientes pa

                ON pa.id=p.paciente_id

            LEFT JOIN profesionales pr

                ON pr.id=p.profesional_id

            WHERE p.fecha BETWEEN ? AND ?

            ORDER BY

                p.fecha,

                p.hora_inicio

        """,

        (

            fecha_inicio,

            fecha_fin,

        ))

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # CONSULTA IA
    # ======================================================

    @staticmethod
    def dataset_motor(

        fecha: str,

    ):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT

                p.id,

                p.prioridad,

                p.duracion,

                p.latitud,

                p.longitud,

                p.servicio,

                p.municipio,

                pa.riesgo_clinico,

                pa.prioridad_domiciliaria

            FROM programaciones p

            INNER JOIN pacientes pa

                ON pa.id=p.paciente_id

            WHERE p.fecha=?

              AND p.estado='PROGRAMADA'

        """,

        (

            fecha,

        ))

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # RUTAS DEL DÍA
    # ======================================================

    @staticmethod
    def rutas_dia(

        fecha: str,

    ):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT

                profesional_id,

                COUNT(*) visitas,

                SUM(duracion) minutos

            FROM programaciones

            WHERE fecha=?

            GROUP BY profesional_id

            ORDER BY profesional_id

        """,

        (

            fecha,

        ))

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # PACIENTES FRECUENTES
    # ======================================================

    @staticmethod
    def pacientes_frecuentes(

        limite: int = 20,

    ):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT

                paciente_id,

                COUNT(*) total

            FROM programaciones

            GROUP BY paciente_id

            ORDER BY total DESC

            LIMIT ?

        """,

        (

            limite,

        ))

        datos = cursor.fetchall()

        conexion.close()

        return datos


    # ======================================================
    # LIMPIEZA DE PROGRAMACIONES
    # ======================================================

    @staticmethod
    def eliminar_historicas(

        fecha_limite: str,

    ):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            DELETE

            FROM programaciones

            WHERE fecha < ?

              AND estado='FINALIZADA'

        """,

        (

            fecha_limite,

        ))

        conexion.commit()

        eliminadas = cursor.rowcount

        conexion.close()

        return eliminadas


    # ======================================================
    # RESUMEN GENERAL
    # ======================================================

    @staticmethod
    def resumen_general():

        conexion = get_connection()

        cursor = conexion.cursor()

        resumen = {}

        cursor.execute(

            "SELECT COUNT(*) FROM programaciones"

        )

        resumen["programaciones"] = cursor.fetchone()[0]

        cursor.execute(

            "SELECT COUNT(*) FROM pacientes"

        )

        resumen["pacientes"] = cursor.fetchone()[0]

        cursor.execute(

            "SELECT COUNT(*) FROM profesionales"

        )

        resumen["profesionales"] = cursor.fetchone()[0]

        cursor.execute("""

            SELECT COUNT(*)

            FROM programaciones

            WHERE estado='FINALIZADA'

        """)

        resumen["finalizadas"] = cursor.fetchone()[0]

        conexion.close()

        return resumen