"""
==========================================================
HomeCare Enterprise
Repositorio de Despacho Inteligente
==========================================================
"""

from __future__ import annotations

from typing import Any

from database.database import (
    consultar,
    consultar_uno,
    ejecutar,
)


class DespachoRepository:

    # =====================================================
    # CONSULTAS
    # =====================================================

    @staticmethod
    def obtener(despacho_id: int):

        return consultar_uno(
            """
            SELECT *
            FROM despachos
            WHERE id=?
            """,
            (despacho_id,),
        )

    @staticmethod
    def listar():

        return consultar(
            """
            SELECT *
            FROM despachos
            ORDER BY fecha,hora_inicio
            """
        )

    @staticmethod
    def pendientes():

        return consultar(
            """
            SELECT *
            FROM despachos
            WHERE estado='PENDIENTE'
            ORDER BY prioridad DESC,
                     fecha,
                     hora_inicio
            """
        )

    @staticmethod
    def en_ruta():

        return consultar(
            """
            SELECT *
            FROM despachos
            WHERE estado='EN_RUTA'
            ORDER BY profesional_id,
                     orden_ruta
            """
        )

    @staticmethod
    def finalizados(fecha: str):

        return consultar(
            """
            SELECT *
            FROM despachos
            WHERE estado='FINALIZADO'
            AND fecha=?
            ORDER BY hora_fin
            """,
            (fecha,),
        )

    @staticmethod
    def por_profesional(
        profesional_id: int,
        fecha: str,
    ):

        return consultar(
            """
            SELECT *
            FROM despachos
            WHERE profesional_id=?
            AND fecha=?
            ORDER BY hora_inicio
            """,
            (
                profesional_id,
                fecha,
            ),
        )
    
        # =====================================================
    # EXISTE
    # =====================================================

    @staticmethod
    def existe(
        despacho_id: int,
    ):

        dato = consultar_uno(
            """
            SELECT COUNT(*) total
            FROM despachos
            WHERE id=?
              AND eliminado=0
            """,
            (
                despacho_id,
            ),
        )

        return dato["total"] > 0


    # =====================================================
    # BUSCAR UUID
    # =====================================================

    @staticmethod
    def buscar_uuid(
        uuid: str,
    ):

        return consultar_uno(
            """
            SELECT *
            FROM despachos
            WHERE uuid=?
              AND eliminado=0
            """,
            (
                uuid,
            ),
        )


    # =====================================================
    # BUSCAR TEXTO
    # =====================================================

    @staticmethod
    def buscar(
        texto: str,
    ):

        filtro = f"%{texto}%"

        return consultar(
            """
            SELECT *

            FROM despachos

            WHERE

                direccion LIKE ?

                OR municipio LIKE ?

                OR departamento LIKE ?

                OR observaciones LIKE ?

            AND eliminado=0

            ORDER BY

                fecha DESC,

                hora_inicio
            """,
            (
                filtro,
                filtro,
                filtro,
                filtro,
            ),
        )


    # =====================================================
    # DESPACHOS DEL DÍA
    # =====================================================

    @staticmethod
    def despacho_dia(
        fecha: str,
    ):

        return consultar(
            """
            SELECT *

            FROM despachos

            WHERE fecha=?
              AND eliminado=0

            ORDER BY

                prioridad DESC,

                hora_inicio
            """,
            (
                fecha,
            ),
        )


    # =====================================================
    # DESPACHOS ENTRE FECHAS
    # =====================================================

    @staticmethod
    def rango_fechas(
        fecha_inicio: str,
        fecha_fin: str,
    ):

        return consultar(
            """
            SELECT *

            FROM despachos

            WHERE fecha BETWEEN ? AND ?
              AND eliminado=0

            ORDER BY

                fecha,

                hora_inicio
            """,
            (
                fecha_inicio,
                fecha_fin,
            ),
        )


    # =====================================================
    # PENDIENTES DE ASIGNACIÓN
    # =====================================================

    @staticmethod
    def pendientes_asignacion():

        return consultar(
            """
            SELECT *

            FROM despachos

            WHERE profesional_id IS NULL
              AND eliminado=0

            ORDER BY

                prioridad DESC,

                fecha,

                hora_inicio
            """
        )


    # =====================================================
    # OBTENER POR PROGRAMACIÓN
    # =====================================================

    @staticmethod
    def por_programacion(
        programacion_id: int,
    ):

        return consultar_uno(
            """
            SELECT *

            FROM despachos

            WHERE programacion_id=?
              AND eliminado=0
            """,
            (
                programacion_id,
            ),
        )
    
        # =====================================================
    # DESPACHOS SIN RUTA
    # =====================================================

    @staticmethod
    def despachos_sin_ruta():

        return consultar(
            """
            SELECT *

            FROM despachos

            WHERE

                (orden_ruta IS NULL
                 OR orden_ruta=0)

                AND eliminado=0

                AND estado IN(

                    'PENDIENTE',

                    'ASIGNADO'

                )

            ORDER BY

                prioridad DESC,

                fecha,

                hora_inicio
            """
        )


    # =====================================================
    # REASIGNAR PROFESIONAL
    # =====================================================

    @staticmethod
    def reasignar_profesional(
        despacho_id: int,
        profesional_id: int,
    ):

        return ejecutar(
            """
            UPDATE despachos

            SET

                profesional_id=?,

                estado='ASIGNADO',

                fecha_actualizacion=CURRENT_TIMESTAMP

            WHERE id=?

            """,
            (

                profesional_id,

                despacho_id,

            ),
        )


    # =====================================================
    # ACTUALIZAR PRIORIDAD
    # =====================================================

    @staticmethod
    def actualizar_prioridad(
        despacho_id: int,
        prioridad: str,
    ):

        return ejecutar(
            """
            UPDATE despachos

            SET

                prioridad=?,

                fecha_actualizacion=CURRENT_TIMESTAMP

            WHERE id=?

            """,
            (

                prioridad,

                despacho_id,

            ),
        )


    # =====================================================
    # MARCAR EN RUTA
    # =====================================================

    @staticmethod
    def iniciar_ruta(
        despacho_id: int,
    ):

        return ejecutar(
            """
            UPDATE despachos

            SET

                estado='EN_RUTA',

                hora_salida=CURRENT_TIMESTAMP,

                fecha_actualizacion=CURRENT_TIMESTAMP

            WHERE id=?

            """,
            (

                despacho_id,

            ),
        )


    # =====================================================
    # MARCAR EN ATENCIÓN
    # =====================================================

    @staticmethod
    def iniciar_atencion(
        despacho_id: int,
    ):

        return ejecutar(
            """
            UPDATE despachos

            SET

                estado='EN_ATENCION',

                hora_llegada=CURRENT_TIMESTAMP,

                fecha_actualizacion=CURRENT_TIMESTAMP

            WHERE id=?

            """,
            (

                despacho_id,

            ),
        )


    # =====================================================
    # FINALIZAR DESPACHO
    # =====================================================

    @staticmethod
    def finalizar(
        despacho_id: int,
    ):

        return ejecutar(
            """
            UPDATE despachos

            SET

                estado='FINALIZADO',

                hora_fin_real=CURRENT_TIMESTAMP,

                fecha_actualizacion=CURRENT_TIMESTAMP

            WHERE id=?

            """,
            (

                despacho_id,

            ),
        )


    # =====================================================
    # CANCELAR DESPACHO
    # =====================================================

    @staticmethod
    def cancelar(
        despacho_id: int,
        motivo: str,
    ):

        return ejecutar(
            """
            UPDATE despachos

            SET

                estado='CANCELADO',

                motivo_cancelacion=?,

                fecha_actualizacion=CURRENT_TIMESTAMP

            WHERE id=?

            """,
            (

                motivo,

                despacho_id,

            ),
        )


    # =====================================================
    # REPROGRAMAR
    # =====================================================

    @staticmethod
    def reprogramar(
        despacho_id: int,
        fecha: str,
        hora_inicio: str,
        hora_fin: str,
    ):

        return ejecutar(
            """
            UPDATE despachos

            SET

                fecha=?,

                hora_inicio=?,

                hora_fin=?,

                estado='REPROGRAMADO',

                fecha_actualizacion=CURRENT_TIMESTAMP

            WHERE id=?

            """,
            (

                fecha,

                hora_inicio,

                hora_fin,

                despacho_id,

            ),
        )
    
        # =====================================================
    # RUTA DEL PROFESIONAL
    # =====================================================

    @staticmethod
    def ruta_profesional(
        profesional_id: int,
        fecha: str,
    ):

        return consultar(
            """
            SELECT *

            FROM despachos

            WHERE profesional_id=?
              AND fecha=?
              AND eliminado=0

            ORDER BY

                orden_ruta,

                hora_inicio
            """,
            (
                profesional_id,
                fecha,
            ),
        )


    # =====================================================
    # ACTUALIZAR ORDEN DE RUTA
    # =====================================================

    @staticmethod
    def actualizar_orden(
        despacho_id: int,
        orden: int,
    ):

        return ejecutar(
            """
            UPDATE despachos

            SET

                orden_ruta=?,

                fecha_actualizacion=CURRENT_TIMESTAMP

            WHERE id=?
            """,
            (
                orden,
                despacho_id,
            ),
        )


    # =====================================================
    # TIEMPO ESTIMADO
    # =====================================================

    @staticmethod
    def actualizar_tiempo_estimado(
        despacho_id: int,
        minutos: int,
    ):

        return ejecutar(
            """
            UPDATE despachos

            SET

                tiempo_estimado=?,

                fecha_actualizacion=CURRENT_TIMESTAMP

            WHERE id=?
            """,
            (
                minutos,
                despacho_id,
            ),
        )


    # =====================================================
    # DISTANCIA ESTIMADA
    # =====================================================

    @staticmethod
    def actualizar_distancia(
        despacho_id: int,
        kilometros: float,
    ):

        return ejecutar(
            """
            UPDATE despachos

            SET

                distancia_estimada=?,

                fecha_actualizacion=CURRENT_TIMESTAMP

            WHERE id=?
            """,
            (
                kilometros,
                despacho_id,
            ),
        )


    # =====================================================
    # POSICIÓN GPS
    # =====================================================

    @staticmethod
    def actualizar_posicion(
        despacho_id: int,
        latitud: float,
        longitud: float,
    ):

        return ejecutar(
            """
            UPDATE despachos

            SET

                latitud_actual=?,

                longitud_actual=?,

                fecha_actualizacion=CURRENT_TIMESTAMP

            WHERE id=?
            """,
            (
                latitud,
                longitud,
                despacho_id,
            ),
        )


    # =====================================================
    # ÚLTIMA POSICIÓN
    # =====================================================

    @staticmethod
    def ultima_posicion(
        despacho_id: int,
    ):

        return consultar_uno(
            """
            SELECT

                latitud_actual,

                longitud_actual,

                fecha_actualizacion

            FROM despachos

            WHERE id=?
            """,
            (
                despacho_id,
            ),
        )


    # =====================================================
    # DISTANCIA TOTAL DE LA RUTA
    # =====================================================

    @staticmethod
    def distancia_total(
        profesional_id: int,
        fecha: str,
    ):

        return consultar_uno(
            """
            SELECT

                COALESCE(
                    SUM(distancia_estimada),
                    0
                ) AS kilometros,

                COUNT(*) AS visitas

            FROM despachos

            WHERE profesional_id=?
              AND fecha=?
              AND eliminado=0
            """,
            (
                profesional_id,
                fecha,
            ),
        )


    # =====================================================
    # TIEMPO TOTAL DE LA RUTA
    # =====================================================

    @staticmethod
    def tiempo_total(
        profesional_id: int,
        fecha: str,
    ):

        return consultar_uno(
            """
            SELECT

                COALESCE(
                    SUM(tiempo_estimado),
                    0
                ) AS minutos

            FROM despachos

            WHERE profesional_id=?
              AND fecha=?
              AND eliminado=0
            """,
            (
                profesional_id,
                fecha,
            ),
        )
    
        # =====================================================
    # PRODUCTIVIDAD DEL DESPACHO
    # =====================================================

    @staticmethod
    def productividad(fecha: str):

        return consultar(
            """
            SELECT

                profesional_id,

                COUNT(*) AS visitas,

                COALESCE(SUM(tiempo_estimado),0) AS minutos,

                COALESCE(SUM(distancia_estimada),0) AS kilometros

            FROM despachos

            WHERE fecha=?
              AND eliminado=0

            GROUP BY profesional_id

            ORDER BY visitas DESC
            """,
            (
                fecha,
            ),
        )


    # =====================================================
    # DESPACHOS POR MUNICIPIO
    # =====================================================

    @staticmethod
    def por_municipio(fecha: str):

        return consultar(
            """
            SELECT

                municipio,

                COUNT(*) total

            FROM despachos

            WHERE fecha=?
              AND eliminado=0

            GROUP BY municipio

            ORDER BY total DESC
            """,
            (
                fecha,
            ),
        )


    # =====================================================
    # DESPACHOS POR PRIORIDAD
    # =====================================================

    @staticmethod
    def por_prioridad(fecha: str):

        return consultar(
            """
            SELECT

                prioridad,

                COUNT(*) total

            FROM despachos

            WHERE fecha=?
              AND eliminado=0

            GROUP BY prioridad

            ORDER BY total DESC
            """,
            (
                fecha,
            ),
        )


    # =====================================================
    # DESPACHOS POR ESTADO
    # =====================================================

    @staticmethod
    def por_estado(fecha: str):

        return consultar(
            """
            SELECT

                estado,

                COUNT(*) total

            FROM despachos

            WHERE fecha=?
              AND eliminado=0

            GROUP BY estado

            ORDER BY estado
            """,
            (
                fecha,
            ),
        )


    # =====================================================
    # TIEMPO PROMEDIO DE ATENCIÓN
    # =====================================================

    @staticmethod
    def tiempo_promedio(fecha: str):

        return consultar_uno(
            """
            SELECT

                AVG(tiempo_estimado) promedio

            FROM despachos

            WHERE fecha=?
              AND eliminado=0
            """,
            (
                fecha,
            ),
        )


    # =====================================================
    # DISTANCIA PROMEDIO
    # =====================================================

    @staticmethod
    def distancia_promedio(fecha: str):

        return consultar_uno(
            """
            SELECT

                AVG(distancia_estimada) promedio

            FROM despachos

            WHERE fecha=?
              AND eliminado=0
            """,
            (
                fecha,
            ),
        )


    # =====================================================
    # EFICIENCIA OPERATIVA
    # =====================================================

    @staticmethod
    def eficiencia(fecha: str):

        return consultar_uno(
            """
            SELECT

                COUNT(*) total,

                SUM(
                    CASE
                        WHEN estado='FINALIZADO'
                        THEN 1
                        ELSE 0
                    END
                ) finalizados,

                SUM(
                    CASE
                        WHEN estado='CANCELADO'
                        THEN 1
                        ELSE 0
                    END
                ) cancelados

            FROM despachos

            WHERE fecha=?
              AND eliminado=0
            """,
            (
                fecha,
            ),
        )


    # =====================================================
    # ÚLTIMOS DESPACHOS
    # =====================================================

    @staticmethod
    def ultimos(
        limite: int = 20,
    ):

        return consultar(
            """
            SELECT *

            FROM despachos

            WHERE eliminado=0

            ORDER BY

                fecha_actualizacion DESC

            LIMIT ?
            """,
            (
                limite,
            ),
        )

    # =====================================================
    # OPERACIONES
    # =====================================================

    @staticmethod
    def crear(datos: dict[str, Any]):

        sql = """
        INSERT INTO despachos
        (
            programacion_id,
            paciente_id,
            profesional_id,
            fecha,
            hora_inicio,
            hora_fin,
            direccion,
            barrio,
            municipio,
            departamento,
            latitud,
            longitud,
            prioridad,
            estado,
            observaciones,
            creado_por
        )
        VALUES
        (
            ?,?,?,?,?,?,
            ?,?,?,?,?,?,
            ?,?,?,?
        )
        """

        return ejecutar(
            sql,
            (
                datos["programacion_id"],
                datos["paciente_id"],
                datos["profesional_id"],
                datos["fecha"],
                datos["hora_inicio"],
                datos["hora_fin"],
                datos["direccion"],
                datos["barrio"],
                datos["municipio"],
                datos["departamento"],
                datos["latitud"],
                datos["longitud"],
                datos["prioridad"],
                datos["estado"],
                datos["observaciones"],
                datos["creado_por"],
            ),
        )

    @staticmethod
    def actualizar_estado(
        despacho_id: int,
        estado: str,
    ):

        return ejecutar(
            """
            UPDATE despachos
            SET estado=?,
                fecha_actualizacion=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (
                estado,
                despacho_id,
            ),
        )

    @staticmethod
    def asignar_profesional(
        despacho_id: int,
        profesional_id: int,
    ):

        return ejecutar(
            """
            UPDATE despachos
            SET profesional_id=?,
                estado='ASIGNADO',
                fecha_actualizacion=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (
                profesional_id,
                despacho_id,
            ),
        )

    @staticmethod
    def eliminar(
        despacho_id: int,
    ):

        return ejecutar(
            """
            UPDATE despachos
            SET eliminado=1
            WHERE id=?
            """,
            (
                despacho_id,
            ),
        )

    # =====================================================
    # DASHBOARD
    # =====================================================

    @staticmethod
    def indicadores():

        return consultar_uno(
            """
            SELECT

            COUNT(*) total,

            SUM(
                CASE
                    WHEN estado='PENDIENTE'
                    THEN 1
                    ELSE 0
                END
            ) pendientes,

            SUM(
                CASE
                    WHEN estado='EN_RUTA'
                    THEN 1
                    ELSE 0
                END
            ) en_ruta,

            SUM(
                CASE
                    WHEN estado='EN_ATENCION'
                    THEN 1
                    ELSE 0
                END
            ) atendiendo,

            SUM(
                CASE
                    WHEN estado='FINALIZADO'
                    THEN 1
                    ELSE 0
                END
            ) finalizados

            FROM despachos

            WHERE eliminado=0
            """
        )
    
        # =====================================================
    # DATASET PARA IA
    # =====================================================

    @staticmethod
    def dataset_ia(
        fecha: str,
    ):

        return consultar(
            """
            SELECT

                d.id,
                d.programacion_id,
                d.profesional_id,
                d.prioridad,
                d.estado,
                d.tiempo_estimado,
                d.distancia_estimada,
                d.latitud,
                d.longitud,
                d.municipio,
                d.departamento

            FROM despachos d

            WHERE d.fecha=?
              AND d.eliminado=0

            ORDER BY

                d.prioridad DESC,

                d.hora_inicio
            """,
            (
                fecha,
            ),
        )


    # =====================================================
    # EXPORTAR
    # =====================================================

    @staticmethod
    def exportar(
        fecha_inicio: str,
        fecha_fin: str,
    ):

        return consultar(
            """
            SELECT *

            FROM despachos

            WHERE fecha BETWEEN ? AND ?

              AND eliminado=0

            ORDER BY

                fecha,

                profesional_id,

                orden_ruta
            """,
            (
                fecha_inicio,
                fecha_fin,
            ),
        )


    # =====================================================
    # RESUMEN GENERAL
    # =====================================================

    @staticmethod
    def resumen_general():

        return consultar_uno(
            """
            SELECT

                COUNT(*) total,

                SUM(
                    CASE
                        WHEN estado='PENDIENTE'
                        THEN 1
                        ELSE 0
                    END
                ) pendientes,

                SUM(
                    CASE
                        WHEN estado='ASIGNADO'
                        THEN 1
                        ELSE 0
                    END
                ) asignados,

                SUM(
                    CASE
                        WHEN estado='EN_RUTA'
                        THEN 1
                        ELSE 0
                    END
                ) en_ruta,

                SUM(
                    CASE
                        WHEN estado='FINALIZADO'
                        THEN 1
                        ELSE 0
                    END
                ) finalizados,

                SUM(
                    CASE
                        WHEN estado='CANCELADO'
                        THEN 1
                        ELSE 0
                    END
                ) cancelados

            FROM despachos

            WHERE eliminado=0
            """
        )


    # =====================================================
    # PROFESIONALES ACTIVOS EN RUTA
    # =====================================================

    @staticmethod
    def profesionales_activos():

        return consultar(
            """
            SELECT DISTINCT

                profesional_id

            FROM despachos

            WHERE estado IN(

                'ASIGNADO',

                'EN_RUTA',

                'EN_ATENCION'

            )

            AND eliminado=0

            ORDER BY profesional_id
            """
        )


    # =====================================================
    # MUNICIPIOS ACTIVOS
    # =====================================================

    @staticmethod
    def municipios_activos():

        return consultar(
            """
            SELECT

                municipio,

                COUNT(*) total

            FROM despachos

            WHERE eliminado=0

            GROUP BY municipio

            ORDER BY total DESC
            """
        )


    # =====================================================
    # LIMPIEZA HISTÓRICA
    # =====================================================

    @staticmethod
    def eliminar_historicos(
        fecha_limite: str,
    ):

        return ejecutar(
            """
            UPDATE despachos

            SET eliminado=1

            WHERE fecha < ?

              AND estado='FINALIZADO'
            """,
            (
                fecha_limite,
            ),
        )


    # =====================================================
    # VALIDAR CONSISTENCIA
    # =====================================================

    @staticmethod
    def validar():

        return consultar_uno(
            """
            SELECT

                COUNT(*) total,

                SUM(

                    CASE

                        WHEN profesional_id IS NULL

                        THEN 1

                        ELSE 0

                    END

                ) sin_profesional,

                SUM(

                    CASE

                        WHEN orden_ruta IS NULL

                        THEN 1

                        ELSE 0

                    END

                ) sin_ruta

            FROM despachos

            WHERE eliminado=0
            """
        )