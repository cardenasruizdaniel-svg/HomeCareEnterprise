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


class ProgramacionRepository:

    """
    Repositorio principal de Programaciones.

    Centraliza todas las operaciones CRUD,
    Agenda Clínica,
    Motor Inteligente,
    Centro de Despacho,
    Dashboard Ejecutivo.
    """

    # ======================================================
    # CONSULTAS GENERALES
    # ======================================================

    @staticmethod
    def listar():

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT

                p.*,

                pa.nombre_completo AS paciente,

                pr.nombre_completo AS profesional

            FROM programaciones p

            LEFT JOIN pacientes pa

                ON pa.id = p.paciente_id

            LEFT JOIN profesionales pr

                ON pr.id = p.profesional_id

            ORDER BY

                p.fecha,

                p.hora_inicio

        """)

        datos = cursor.fetchall()

        conexion.close()

        return datos

    # ======================================================

    @staticmethod
    def obtener(

        programacion_id: int,

    ):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT *

            FROM programaciones

            WHERE id=?

        """,

        (

            programacion_id,

        ))

        dato = cursor.fetchone()

        conexion.close()

        return dato

    # ======================================================

    @staticmethod
    def buscar_uuid(

        uuid: str,

    ):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT *

            FROM programaciones

            WHERE uuid=?

        """,

        (

            uuid,

        ))

        dato = cursor.fetchone()

        conexion.close()

        return dato

    # ======================================================

    @staticmethod
    def existe(

        programacion_id: int,

    ) -> bool:

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT COUNT(*)

            FROM programaciones

            WHERE id=?

        """,

        (

            programacion_id,

        ))

        existe = cursor.fetchone()[0] > 0

        conexion.close()

        return existe

    # ======================================================

    @staticmethod
    def crear(

        datos: dict[str, Any],

    ):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            INSERT INTO programaciones(

                uuid,

                paciente_id,

                profesional_id,

                servicio,

                procedimiento,

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

                observaciones,

                usuario_creacion

            )

            VALUES(

                :uuid,

                :paciente_id,

                :profesional_id,

                :servicio,

                :procedimiento,

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

                :observaciones,

                :usuario_creacion

            )

        """, datos)

        conexion.commit()

        nuevo_id = cursor.lastrowid

        conexion.close()

        return nuevo_id

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

                pa.nombre_completo AS paciente,

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
    # AGENDA POR PROFESIONAL
    # ======================================================

    @staticmethod
    def agenda_profesional(

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
    # AGENDA ENTRE FECHAS
    # ======================================================

    @staticmethod
    def agenda_rango(

        fecha_inicio: str,

        fecha_fin: str,

    ):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT *

            FROM programaciones

            WHERE fecha BETWEEN ? AND ?

            ORDER BY

                fecha,

                hora_inicio

        """,

        (

            fecha_inicio,

            fecha_fin,

        ))

        datos = cursor.fetchall()

        conexion.close()

        return datos


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

                pa.nombre_completo AS paciente

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

                pa.nombre_completo AS paciente,

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

                pa.nombre_completo AS paciente,

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
    # PROGRAMACIONES POR UUID
    # ======================================================

    @staticmethod
    def obtener_uuid(

        uuid: str,

    ):

        conexion = get_connection()

        cursor = conexion.cursor()

        cursor.execute("""

            SELECT *

            FROM programaciones

            WHERE uuid=?

        """,

        (

            uuid,

        ))

        dato = cursor.fetchone()

        conexion.close()

        return dato


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